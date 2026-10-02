"""
SwachhLoop AI — Notifications Routes
========================================
Endpoints:
    GET   /api/notifications         — current user's notifications
    PATCH /api/notifications/{id}/read — mark one as read
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_current_user
from backend.db.session import get_db
from backend.models.user import User
from backend.repositories import notification_repo
from backend.schemas.notification import NotificationResponse

router = APIRouter()


@router.get(
    "",
    response_model=list[NotificationResponse],
    summary="Get notifications for the current user",
)
async def get_notifications(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[NotificationResponse]:
    notifications = await notification_repo.get_notifications_for_user(
        db, current_user.id, limit=limit
    )
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    summary="Mark a notification as read",
)
async def mark_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> NotificationResponse:
    notif = await notification_repo.mark_notification_read(db, notification_id, current_user.id)
    if notif is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found.",
        )
    return NotificationResponse.model_validate(notif)
