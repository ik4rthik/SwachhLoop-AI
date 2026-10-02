"""
SwachhLoop AI — Stats Routes
================================
Endpoints:
    GET /api/stats/municipal — dashboard stats for municipal staff and admin
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import require_staff_or_admin
from backend.db.session import get_db
from backend.models.user import User, UserRole
from backend.repositories.complaint_repo import get_complaint_counts_by_status
from backend.repositories.user_repo import get_users_by_role
from backend.schemas.admin import MunicipalStats

router = APIRouter()


@router.get(
    "/municipal",
    response_model=MunicipalStats,
    summary="Get municipal dashboard statistics (staff/admin only)",
)
async def municipal_stats(
    current_user: User = Depends(require_staff_or_admin),
    db: AsyncSession = Depends(get_db),
) -> MunicipalStats:
    """Real-time stats derived from the database."""
    counts = await get_complaint_counts_by_status(db)
    cleaners = await get_users_by_role(db, UserRole.CLEANER)

    # Count cleaners with active tasks (IN_PROGRESS)
    from backend.repositories.task_repo import get_tasks
    active_tasks = await get_tasks(db, status="IN_PROGRESS")
    active_cleaner_ids = {t.assigned_to for t in active_tasks if t.assigned_to}

    total = sum(counts.values())

    return MunicipalStats(
        total_complaints=total,
        pending=counts.get("SUBMITTED", 0),
        validated=counts.get("VALIDATED", 0),
        assigned=counts.get("ASSIGNED", 0),
        cleaning=counts.get("CLEANING", 0),
        verification=counts.get("VERIFICATION", 0),
        resolved=counts.get("RESOLVED", 0),
        escalated=counts.get("ESCALATED", 0),
        avg_resolution_hours=0.0,   # Phase 4: compute from resolved complaint timestamps
        cleaners_available=len(cleaners) - len(active_cleaner_ids),
        cleaners_on_task=len(active_cleaner_ids),
    )
