"""
SwachhLoop AI — Task Repository
==================================
All database operations for cleaning_tasks.
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.task import CleaningTask, TaskStatus


async def create_task(
    db: AsyncSession,
    complaint_id: int,
    assigned_to: int | None = None,
    assigned_by: int | None = None,
    notes: str | None = None,
) -> CleaningTask:
    task = CleaningTask(
        complaint_id=complaint_id,
        assigned_to=assigned_to,
        assigned_by=assigned_by,
        status=TaskStatus.PENDING,
        notes=notes,
        assigned_at=datetime.now(timezone.utc) if assigned_to else None,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def get_task_by_id(
    db: AsyncSession, task_id: int, load_complaint: bool = True
) -> CleaningTask | None:
    stmt = select(CleaningTask).where(CleaningTask.id == task_id)
    if load_complaint:
        stmt = stmt.options(selectinload(CleaningTask.complaint))
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_tasks(
    db: AsyncSession,
    cleaner_id: int | None = None,
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[CleaningTask]:
    stmt = (
        select(CleaningTask)
        .options(selectinload(CleaningTask.complaint))
        .order_by(CleaningTask.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    if cleaner_id is not None:
        stmt = stmt.where(CleaningTask.assigned_to == cleaner_id)
    if status is not None:
        stmt = stmt.where(CleaningTask.status == status.upper())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_task_status(
    db: AsyncSession, task_id: int, new_status: TaskStatus, actor_id: int | None = None
) -> CleaningTask | None:
    task = await get_task_by_id(db, task_id, load_complaint=False)
    if task is None:
        return None
    task.status = new_status
    if new_status == TaskStatus.COMPLETED:
        task.completed_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(task)
    return task


async def update_task_after_image(
    db: AsyncSession, task_id: int, after_image_url: str
) -> CleaningTask | None:
    task = await get_task_by_id(db, task_id, load_complaint=False)
    if task is None:
        return None
    task.after_image_url = after_image_url
    await db.flush()
    await db.refresh(task)
    return task


async def get_task_by_complaint_id(
    db: AsyncSession, complaint_id: int
) -> CleaningTask | None:
    result = await db.execute(
        select(CleaningTask).where(CleaningTask.complaint_id == complaint_id)
    )
    return result.scalar_one_or_none()
