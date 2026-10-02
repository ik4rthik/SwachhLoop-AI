"""
SwachhLoop AI — Notification Schemas
======================================
Pydantic request/response models for /api/notifications.
"""

from datetime import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    """A single notification."""
    id: int
    user_id: int
    type: str
    title: str
    message: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}
