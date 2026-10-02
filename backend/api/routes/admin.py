"""
SwachhLoop AI — Admin Routes
================================
Endpoints (admin-only):
    GET    /api/admin/users         — list all users
    PATCH  /api/admin/users/{id}    — toggle user active status
    GET    /api/admin/audit-log     — audit log
    GET    /api/admin/health        — system component health
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import require_admin
from backend.db.session import get_db
from backend.models.user import User, UserRole
from backend.repositories import audit_log_repo, user_repo
from backend.schemas.admin import AuditLogResponse, CreateUserAdminRequest, SystemHealthItem, UserAdminResponse
from backend.services.audit_service import (
    ACTION_CREATE_USER, ACTION_DEACTIVATE_USER, ACTION_REACTIVATE_USER, log_event
)
from backend.services.auth_service import hash_password

router = APIRouter()


# ---------------------------------------------------------------------------
# POST /api/admin/users
# ---------------------------------------------------------------------------

@router.post(
    "/users",
    response_model=UserAdminResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user account (admin only)",
)
async def create_user_by_admin(
    body: CreateUserAdminRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserAdminResponse:
    """
    Secure endpoint for administrators to create privileged user accounts
    (Cleaners, Municipal Staff, Admins, or Citizens).
    """
    existing = await user_repo.get_user_by_email(db, body.email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    try:
        role = UserRole(body.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid role: {body.role!r}",
        )

    user = await user_repo.create_user(
        db=db,
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=role,
        phone=body.phone,
        ward=body.ward,
        employee_id=body.employee_id,
        department=body.department,
    )

    await log_event(
        db,
        action=ACTION_CREATE_USER,
        actor_id=current_user.id,
        resource_type="user",
        resource_id=str(user.id),
        detail=f"Admin created {role.value} account: {user.email}",
    )

    return UserAdminResponse.model_validate(user)


# ---------------------------------------------------------------------------
# GET /api/admin/users
# ---------------------------------------------------------------------------

@router.get(
    "/users",
    response_model=list[UserAdminResponse],
    summary="List all users (admin only)",
)
async def list_users(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[UserAdminResponse]:
    users = await user_repo.get_all_users(db)
    return [UserAdminResponse.model_validate(u) for u in users]


# ---------------------------------------------------------------------------
# PATCH /api/admin/users/{id}
# ---------------------------------------------------------------------------

@router.patch(
    "/users/{user_id}",
    response_model=UserAdminResponse,
    summary="Toggle user active status (admin only)",
)
async def toggle_user_active(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> UserAdminResponse:
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate your own account.",
        )

    user = await user_repo.update_user_active(db, user_id, is_active)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    action = ACTION_REACTIVATE_USER if is_active else ACTION_DEACTIVATE_USER
    await log_event(
        db,
        action=action,
        actor_id=current_user.id,
        resource_type="user",
        resource_id=str(user_id),
        detail=f"User {user.email} {'reactivated' if is_active else 'deactivated'}",
    )

    return UserAdminResponse.model_validate(user)


# ---------------------------------------------------------------------------
# GET /api/admin/audit-log
# ---------------------------------------------------------------------------

@router.get(
    "/audit-log",
    response_model=list[AuditLogResponse],
    summary="Get audit log (admin only)",
)
async def get_audit_log(
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AuditLogResponse]:
    entries = await audit_log_repo.get_audit_log(db, limit=limit, offset=offset)
    result = []
    for e in entries:
        actor_name = e.actor.full_name if e.actor else "System"
        result.append(AuditLogResponse(
            id=e.id,
            actor_id=e.actor_id,
            actor_name=actor_name,
            action=e.action,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            detail=e.detail,
            ip_address=e.ip_address,
            created_at=e.created_at,
        ))
    return result


# ---------------------------------------------------------------------------
# GET /api/admin/health
# ---------------------------------------------------------------------------

@router.get(
    "/health",
    response_model=list[SystemHealthItem],
    summary="System component health (admin only)",
)
async def system_health(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[SystemHealthItem]:
    """
    Returns real status for DB; stubs for AI/RAG/Route components.
    Phase 4+ will populate the AI service statuses.
    """
    # Test DB connectivity
    db_status = "Online"
    db_latency = "—"
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        db_status = "Online"
        db_latency = "<5ms"
    except Exception:  # pragma: no cover
        db_status = "Error"

    return [
        SystemHealthItem(service="Backend API", status="Online", latency="<5ms", uptime="—", icon="🟢"),
        SystemHealthItem(service="Database", status=db_status, latency=db_latency, uptime="—", icon="🟢" if db_status == "Online" else "🔴"),
        SystemHealthItem(service="AI Services", status="Stub (Phase 4)", latency="—", uptime="—", icon="🟡"),
        SystemHealthItem(service="RAG Pipeline", status="Stub (Phase 4)", latency="—", uptime="—", icon="🟡"),
        SystemHealthItem(service="Route Optimizer", status="Stub (Phase 4)", latency="—", uptime="—", icon="🟡"),
    ]
