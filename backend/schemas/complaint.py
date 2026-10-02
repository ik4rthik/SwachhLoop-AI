"""
SwachhLoop AI — Complaint Schemas
===================================
Pydantic request/response models for the /api/complaints/* endpoints.
"""

from datetime import datetime
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------

class ComplaintCreate(BaseModel):
    """POST /api/complaints — body (image is uploaded separately as multipart)"""
    title: str | None = Field(default=None, max_length=255)
    description: str | None = Field(default=None)
    latitude: float | None = None
    longitude: float | None = None
    location_label: str | None = Field(default=None, max_length=300)
    waste_type: str | None = Field(default=None, max_length=100)
    priority: str = Field(default="MEDIUM")

    @classmethod
    def validate_priority(cls, v: str) -> str:
        allowed = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"priority must be one of: {', '.join(sorted(allowed))}")
        return v


class ComplaintStatusUpdate(BaseModel):
    """PATCH /api/complaints/{id}/status"""
    status: str

    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"SUBMITTED", "VALIDATED", "ASSIGNED", "CLEANING", "VERIFICATION", "RESOLVED", "ESCALATED"}
        v = v.upper()
        if v not in allowed:
            raise ValueError(f"status must be one of: {', '.join(sorted(allowed))}")
        return v


class ComplaintAssign(BaseModel):
    """PATCH /api/complaints/{id}/assign"""
    cleaner_id: int


# ---------------------------------------------------------------------------
# Responses
# ---------------------------------------------------------------------------

class CitizenSummary(BaseModel):
    """Embedded citizen info in a complaint response."""
    id: int
    full_name: str
    email: str

    model_config = {"from_attributes": True}


class ComplaintResponse(BaseModel):
    """Full complaint detail response."""
    id: int
    citizen_id: int
    citizen: CitizenSummary | None = None
    title: str | None
    description: str | None
    image_url: str | None
    latitude: float | None
    longitude: float | None
    location_label: str | None
    reported_at: datetime
    updated_at: datetime
    status: str
    priority: str
    waste_type: str | None
    waste_confidence: float | None
    assigned_cleaner: str | None = None
    task_id: int | None = None

    model_config = {"from_attributes": True}


class MapMarker(BaseModel):
    """Map marker returned by GET /api/complaints/map-markers"""
    id: int
    lat: float | None
    lon: float | None
    type: str          # priority level used as visual type
    label: str | None
    complaint_id: int
