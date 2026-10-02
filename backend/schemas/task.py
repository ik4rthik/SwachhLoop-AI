"""
SwachhLoop AI — Task Schemas
==============================
Pydantic request/response models for the /api/tasks/* endpoints.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class TaskStatusUpdate(BaseModel):
    """PATCH /api/tasks/{id}"""
    status: str = Field(description="PENDING | IN_PROGRESS | COMPLETED | CANCELLED")


class TaskResponse(BaseModel):
    """Full cleaning task detail response."""
    id: int
    complaint_id: int
    assigned_to: int | None
    assigned_by: int | None
    status: str
    estimated_time: str | None
    distance: str | None
    notes: str | None
    before_image_url: str | None
    after_image_url: str | None
    assigned_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Embedded complaint info for display
    complaint_title: str | None = None
    complaint_location: str | None = None
    complaint_latitude: float | None = None
    complaint_longitude: float | None = None
    complaint_priority: str | None = None
    complaint_waste_type: str | None = None

    model_config = {"from_attributes": True}
