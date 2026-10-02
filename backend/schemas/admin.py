"""
SwachhLoop AI — Admin & Stats Schemas
========================================
Pydantic response models for /api/admin/* and /api/stats/* endpoints.
"""

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


class CreateUserAdminRequest(BaseModel):
    """POST /api/admin/users — Admin creates any user role."""
    email: EmailStr
    password: str = Field(min_length=8, description="Minimum 8 characters")
    full_name: str = Field(min_length=2, max_length=255)
    role: str = Field(description="citizen | cleaner | municipal_staff | admin")
    phone: str | None = Field(default=None, max_length=20)
    ward: str | None = Field(default=None, max_length=100)
    employee_id: str | None = Field(default=None, max_length=50)
    department: str | None = Field(default=None, max_length=100)

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"citizen", "cleaner", "municipal_staff", "admin"}
        v_clean = v.strip().lower()
        if v_clean not in allowed:
            raise ValueError(f"role must be one of: {', '.join(sorted(allowed))}")
        return v_clean


class UserAdminResponse(BaseModel):
    """Admin view of a user — includes all fields."""
    id: int
    email: str
    full_name: str
    role: str
    phone: str | None
    ward: str | None
    employee_id: str | None
    department: str | None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class AuditLogResponse(BaseModel):
    """A single audit log entry."""
    id: int
    actor_id: int | None
    actor_name: str | None = None  # Populated by join
    action: str
    resource_type: str | None
    resource_id: str | None
    detail: str | None
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemHealthItem(BaseModel):
    """One component in the system health view."""
    service: str
    status: str
    latency: str
    uptime: str
    icon: str


class MunicipalStats(BaseModel):
    """Dashboard stats for Municipal Staff and Admin."""
    total_complaints: int
    pending: int
    validated: int
    assigned: int
    cleaning: int
    verification: int
    resolved: int
    escalated: int
    avg_resolution_hours: float
    cleaners_available: int
    cleaners_on_task: int
