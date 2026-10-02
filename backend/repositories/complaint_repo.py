"""
SwachhLoop AI — Complaint Repository
=======================================
All database operations related to the complaints table.
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.complaint import Complaint, ComplaintPriority, ComplaintStatus


async def create_complaint(
    db: AsyncSession,
    citizen_id: int,
    title: str | None = None,
    description: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    location_label: str | None = None,
    waste_type: str | None = None,
    priority: ComplaintPriority = ComplaintPriority.MEDIUM,
    image_url: str | None = None,
) -> Complaint:
    complaint = Complaint(
        citizen_id=citizen_id,
        title=title,
        description=description,
        latitude=latitude,
        longitude=longitude,
        location_label=location_label,
        waste_type=waste_type,
        priority=priority,
        image_url=image_url,
        status=ComplaintStatus.SUBMITTED,
        waste_confidence=None,
    )
    db.add(complaint)
    await db.flush()
    await db.refresh(complaint)
    return complaint


async def get_complaint_by_id(
    db: AsyncSession, complaint_id: int, load_citizen: bool = True
) -> Complaint | None:
    stmt = select(Complaint).where(Complaint.id == complaint_id)
    if load_citizen:
        stmt = stmt.options(selectinload(Complaint.citizen))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_complaints(
    db: AsyncSession,
    citizen_id: int | None = None,
    status: str | None = None,
    priority: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Complaint]:
    stmt = (
        select(Complaint)
        .options(selectinload(Complaint.citizen))
        .order_by(Complaint.reported_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if citizen_id is not None:
        stmt = stmt.where(Complaint.citizen_id == citizen_id)
    if status is not None:
        stmt = stmt.where(Complaint.status == status.upper())
    if priority is not None:
        stmt = stmt.where(Complaint.priority == priority.upper())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_complaint_status(
    db: AsyncSession, complaint_id: int, new_status: ComplaintStatus
) -> Complaint | None:
    complaint = await get_complaint_by_id(db, complaint_id, load_citizen=False)
    if complaint is None:
        return None
    complaint.status = new_status
    await db.flush()
    await db.refresh(complaint)
    return complaint


async def get_complaint_counts_by_status(db: AsyncSession) -> dict[str, int]:
    """Returns {status_value: count} for dashboard stats."""
    result = await db.execute(
        select(Complaint.status, func.count(Complaint.id))
        .group_by(Complaint.status)
    )
    return {str(row[0].value): row[1] for row in result.all()}
