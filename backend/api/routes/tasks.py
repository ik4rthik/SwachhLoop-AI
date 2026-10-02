"""
SwachhLoop AI — Tasks Routes
================================
Endpoints:
    GET    /api/tasks         — list tasks (role-filtered)
    GET    /api/tasks/{id}    — get single task
    PATCH  /api/tasks/{id}    — update status (cleaner: own tasks only)
    POST   /api/tasks/{id}/evidence — upload after-image (cleaner)
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user, require_staff_or_admin
from backend.db.session import get_db
from backend.models.task import TaskStatus
from backend.models.user import User, UserRole
from backend.repositories import task_repo
from backend.schemas.task import TaskResponse, TaskStatusUpdate
from backend.services.audit_service import ACTION_UPDATE_TASK_STATUS, ACTION_UPLOAD_EVIDENCE, log_event
from backend.services.storage_service import save_upload

logger = logging.getLogger(__name__)
router = APIRouter()


def _task_to_response(task) -> TaskResponse:
    """Build TaskResponse with embedded complaint fields."""
    c = task.complaint if hasattr(task, "complaint") and task.complaint else None
    return TaskResponse(
        id=task.id,
        complaint_id=task.complaint_id,
        assigned_to=task.assigned_to,
        assigned_by=task.assigned_by,
        status=task.status.value if hasattr(task.status, "value") else task.status,
        estimated_time=task.estimated_time,
        distance=task.distance,
        notes=task.notes,
        before_image_url=task.before_image_url,
        after_image_url=task.after_image_url,
        assigned_at=task.assigned_at,
        completed_at=task.completed_at,
        created_at=task.created_at,
        updated_at=task.updated_at,
        complaint_title=c.title if c else None,
        complaint_location=c.location_label if c else None,
        complaint_latitude=c.latitude if c else None,
        complaint_longitude=c.longitude if c else None,
        complaint_priority=c.priority.value if c and c.priority else None,
        complaint_waste_type=c.waste_type if c else None,
    )


# ---------------------------------------------------------------------------
# GET /api/tasks
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[TaskResponse],
    summary="List cleaning tasks (role-filtered)",
)
async def list_tasks(
    task_status: str | None = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TaskResponse]:
    """
    - Cleaner: sees only tasks assigned to them.
    - Staff / Admin: sees all tasks.
    """
    cleaner_id = None
    if current_user.role == UserRole.CLEANER:
        cleaner_id = current_user.id

    tasks = await task_repo.get_tasks(
        db, cleaner_id=cleaner_id, status=task_status, limit=limit, offset=offset
    )
    return [_task_to_response(t) for t in tasks]


# ---------------------------------------------------------------------------
# GET /api/tasks/{id}
# ---------------------------------------------------------------------------

@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get a single cleaning task",
)
async def get_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    task = await task_repo.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    # Cleaners can only see their own tasks
    if current_user.role == UserRole.CLEANER and task.assigned_to != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    return _task_to_response(task)


# ---------------------------------------------------------------------------
# PATCH /api/tasks/{id}
# ---------------------------------------------------------------------------

@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update task status",
)
async def update_task(
    task_id: int,
    body: TaskStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """
    Cleaners can update their own tasks.
    Staff/Admin can update any task.
    """
    task = await task_repo.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    # Cleaners can only update their own tasks
    if current_user.role == UserRole.CLEANER and task.assigned_to != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    try:
        new_status = TaskStatus(body.status.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid status: {body.status!r}. Use PENDING, IN_PROGRESS, COMPLETED, or CANCELLED.",
        )

    task = await task_repo.update_task_status(db, task_id, new_status, actor_id=current_user.id)

    # Update the linked complaint status when task is completed
    if new_status == TaskStatus.COMPLETED:
        from backend.repositories.complaint_repo import update_complaint_status
        from backend.models.complaint import ComplaintStatus
        await update_complaint_status(db, task.complaint_id, ComplaintStatus.VERIFICATION)

    await log_event(
        db,
        action=ACTION_UPDATE_TASK_STATUS,
        actor_id=current_user.id,
        resource_type="task",
        resource_id=str(task_id),
        detail=f"Task status changed to {new_status.value}",
        ip_address=request.client.host if request.client else None,
    )

    task = await task_repo.get_task_by_id(db, task_id)
    return _task_to_response(task)


# ---------------------------------------------------------------------------
# POST /api/tasks/{id}/evidence
# ---------------------------------------------------------------------------

@router.post(
    "/{task_id}/evidence",
    response_model=TaskResponse,
    summary="Upload cleanup evidence (after-image)",
)
async def upload_evidence(
    task_id: int,
    request: Request,
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TaskResponse:
    """Cleaner uploads the after-cleanup photo for a completed task."""
    task = await task_repo.get_task_by_id(db, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found.")

    if current_user.role == UserRole.CLEANER and task.assigned_to != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    file_bytes = await image.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image must be smaller than 10 MB.",
        )

    url = await save_upload(file_bytes, image.filename or "evidence.jpg", image.content_type or "image/jpeg")
    task = await task_repo.update_task_after_image(db, task_id, url)

    await log_event(
        db,
        action=ACTION_UPLOAD_EVIDENCE,
        actor_id=current_user.id,
        resource_type="task",
        resource_id=str(task_id),
        detail=f"After-image uploaded: {url}",
        ip_address=request.client.host if request.client else None,
    )

    task = await task_repo.get_task_by_id(db, task_id)
    return _task_to_response(task)
