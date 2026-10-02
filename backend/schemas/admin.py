"""
SwachhLoop AI — Admin & Stats Schemas
========================================
Pydantic response models for /api/admin/* and /api/stats/* endpoints.
"""

from datetime import datetime
from pydantic import BaseModel


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
