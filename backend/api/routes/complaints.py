"""
SwachhLoop AI — Complaints Routes
====================================
Endpoints:
    POST   /api/complaints                — submit new complaint (citizen)
    GET    /api/complaints                — list complaints (role-filtered)
    GET    /api/complaints/map-markers    — map data
    GET    /api/complaints/{id}           — get single complaint
    PATCH  /api/complaints/{id}/status    — update status (staff/admin)
    PATCH  /api/complaints/{id}/assign    — assign task (staff/admin)
"""

import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user, require_staff_or_admin
from backend.db.session import get_db
from backend.models.complaint import ComplaintPriority, ComplaintStatus
from backend.models.task import TaskStatus
from backend.models.user import User, UserRole
from backend.repositories import complaint_repo, task_repo, notification_repo
from backend.schemas.complaint import ComplaintResponse, MapMarker
from backend.services.audit_service import (
    ACTION_ASSIGN_TASK, ACTION_SUBMIT_COMPLAINT, ACTION_UPDATE_COMPLAINT_STATUS, log_event
)
from backend.services.storage_service import save_upload
from backend.models.notification import NotificationType

logger = logging.getLogger(__name__)
router = APIRouter()


def _complaint_to_response(c) -> ComplaintResponse:
    return ComplaintResponse.model_validate(c)


# ---------------------------------------------------------------------------
# POST /api/complaints
# ---------------------------------------------------------------------------

@router.post(
    "",
    response_model=ComplaintResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a new waste complaint",
)
async def submit_complaint(
    request: Request,
    title: str | None = Form(default=None),
    description: str | None = Form(default=None),
    latitude: float | None = Form(default=None),
    longitude: float | None = Form(default=None),
    location_label: str | None = Form(default=None),
    waste_type: str | None = Form(default=None),
    priority: str = Form(default="MEDIUM"),
    image: UploadFile | None = File(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComplaintResponse:
    """
    Citizen submits a waste complaint.
    Optional image upload is stored via storage_service.
    AI waste_confidence is left null — Phase 4 will populate it.
    """
    # Validate priority
    try:
        priority_enum = ComplaintPriority(priority.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid priority: {priority!r}. Use LOW, MEDIUM, HIGH, or CRITICAL.",
        )

    # Handle image upload
    image_url: str | None = None
    if image is not None and image.filename:
        file_bytes = await image.read()
        if len(file_bytes) > 10 * 1024 * 1024:  # 10 MB limit
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Image must be smaller than 10 MB.",
            )
        image_url = await save_upload(file_bytes, image.filename, image.content_type or "image/jpeg")

    complaint = await complaint_repo.create_complaint(
        db=db,
        citizen_id=current_user.id,
        title=title,
        description=description,
        latitude=latitude,
        longitude=longitude,
        location_label=location_label,
        waste_type=waste_type,
        priority=priority_enum,
        image_url=image_url,
    )

    await log_event(
        db,
        action=ACTION_SUBMIT_COMPLAINT,
        actor_id=current_user.id,
        resource_type="complaint",
        resource_id=str(complaint.id),
        detail=f"Complaint submitted: {title or 'Untitled'}",
        ip_address=request.client.host if request.client else None,
    )

    # Reload with citizen relationship
    complaint = await complaint_repo.get_complaint_by_id(db, complaint.id)
    logger.info(f"Complaint {complaint.id} submitted by user {current_user.id}")
    return _complaint_to_response(complaint)


# ---------------------------------------------------------------------------
# GET /api/complaints/map-markers  (must be before /{id} to avoid routing conflict)
# ---------------------------------------------------------------------------

@router.get(
    "/map-markers",
    response_model=list[MapMarker],
    summary="Get complaint locations for map display",
)
async def get_map_markers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[MapMarker]:
    """All complaints with lat/lon for map display. Available to all authenticated users."""
    complaints = await complaint_repo.get_complaints(db, limit=500)
    markers = []
    for c in complaints:
        if c.latitude is None or c.longitude is None:
            continue
        markers.append(MapMarker(
            id=c.id,
            lat=c.latitude,
            lon=c.longitude,
            type=c.priority.value if c.priority else "MEDIUM",
            label=c.title or c.location_label,
            complaint_id=c.id,
        ))
    return markers


# ---------------------------------------------------------------------------
# GET /api/complaints
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[ComplaintResponse],
    summary="List complaints (role-filtered)",
)
async def list_complaints(
    status: str | None = None,
    priority: str | None = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ComplaintResponse]:
    """
    - Citizen: sees only their own complaints.
    - Staff / Admin: sees all complaints.
    - Cleaner: sees complaints linked to their tasks (via tasks endpoint).
    """
    citizen_id = None
    if current_user.role == UserRole.CITIZEN:
        citizen_id = current_user.id

    complaints = await complaint_repo.get_complaints(
        db,
        citizen_id=citizen_id,
        status=status,
        priority=priority,
        limit=limit,
        offset=offset,
    )
    return [_complaint_to_response(c) for c in complaints]


# ---------------------------------------------------------------------------
# GET /api/complaints/{id}
# ---------------------------------------------------------------------------

@router.get(
    "/{complaint_id}",
    response_model=ComplaintResponse,
    summary="Get a single complaint",
)
async def get_complaint(
    complaint_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ComplaintResponse:
    complaint = await complaint_repo.get_complaint_by_id(db, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    # Citizens can only view their own complaints
    if current_user.role == UserRole.CITIZEN and complaint.citizen_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return _complaint_to_response(complaint)


# ---------------------------------------------------------------------------
# PATCH /api/complaints/{id}/status
# ---------------------------------------------------------------------------

@router.patch(
    "/{complaint_id}/status",
    response_model=ComplaintResponse,
    summary="Update complaint status (staff/admin only)",
)
async def update_status(
    complaint_id: int,
    new_status: str,
    request: Request,
    current_user: User = Depends(require_staff_or_admin),
    db: AsyncSession = Depends(get_db),
) -> ComplaintResponse:
    try:
        status_enum = ComplaintStatus(new_status.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status: {new_status!r}",
        )

    complaint = await complaint_repo.update_complaint_status(db, complaint_id, status_enum)
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    await log_event(
        db,
        action=ACTION_UPDATE_COMPLAINT_STATUS,
        actor_id=current_user.id,
        resource_type="complaint",
        resource_id=str(complaint_id),
        detail=f"Status changed to {new_status.upper()}",
        ip_address=request.client.host if request.client else None,
    )

    complaint = await complaint_repo.get_complaint_by_id(db, complaint_id)
    return _complaint_to_response(complaint)


# ---------------------------------------------------------------------------
# PATCH /api/complaints/{id}/assign
# ---------------------------------------------------------------------------

@router.patch(
    "/{complaint_id}/assign",
    response_model=ComplaintResponse,
    summary="Assign complaint to a cleaner and create a task (staff/admin only)",
)
async def assign_complaint(
    complaint_id: int,
    cleaner_id: int,
    request: Request,
    current_user: User = Depends(require_staff_or_admin),
    db: AsyncSession = Depends(get_db),
) -> ComplaintResponse:
    complaint = await complaint_repo.get_complaint_by_id(db, complaint_id, load_citizen=False)
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found.")

    # Check cleaner exists
    from backend.repositories.user_repo import get_user_by_id
    cleaner = await get_user_by_id(db, cleaner_id)
    if cleaner is None or cleaner.role != UserRole.CLEANER:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cleaner not found.")

    # Create or update task
    existing_task = await task_repo.get_task_by_complaint_id(db, complaint_id)
    if existing_task is None:
        await task_repo.create_task(
            db=db,
            complaint_id=complaint_id,
            assigned_to=cleaner_id,
            assigned_by=current_user.id,
        )
    else:
        existing_task.assigned_to = cleaner_id
        existing_task.assigned_by = current_user.id
        existing_task.status = TaskStatus.PENDING
        await db.flush()

    # Update complaint status to ASSIGNED
    await complaint_repo.update_complaint_status(db, complaint_id, ComplaintStatus.ASSIGNED)

    # Notify the cleaner
    await notification_repo.create_notification(
        db=db,
        user_id=cleaner_id,
        title="New Task Assigned",
        message=f"You have been assigned a new cleaning task for complaint #{complaint_id}.",
        type=NotificationType.INFO,
    )

    await log_event(
        db,
        action=ACTION_ASSIGN_TASK,
        actor_id=current_user.id,
        resource_type="complaint",
        resource_id=str(complaint_id),
        detail=f"Assigned to cleaner {cleaner_id}",
        ip_address=request.client.host if request.client else None,
    )

    complaint = await complaint_repo.get_complaint_by_id(db, complaint_id)
    return _complaint_to_response(complaint)
