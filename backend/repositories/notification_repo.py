"""
SwachhLoop AI — Notification Repository
==========================================
Database operations for user notifications.
"""

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.notification import Notification, NotificationType


async def create_notification(
    db: AsyncSession,
    user_id: int,
    title: str,
    message: str,
    type: NotificationType = NotificationType.INFO,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        is_read=False,
    )
    db.add(notif)
    await db.flush()
    await db.refresh(notif)
    return notif


async def get_notifications_for_user(
    db: AsyncSession,
    user_id: int,
    limit: int = 50,
) -> list[Notification]:
    result = await db.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def mark_notification_read(
    db: AsyncSession, notification_id: int, user_id: int
) -> Notification | None:
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
    )
    notif = result.scalar_one_or_none()
    if notif is None:
        return None
    notif.is_read = True
    await db.flush()
    await db.refresh(notif)
    return notif
