"""
SwachhLoop AI — Shared Pydantic Schemas
========================================
These are the common request/response models used across the API.
Domain-specific models (complaints, routes, etc.) will be added
in their respective feature phases.
"""

from datetime import datetime
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Generic API response wrapper
# ---------------------------------------------------------------------------

class APIResponse(BaseModel):
    """Standard envelope for all API responses."""
    success: bool
    message: str
    data: dict | list | None = None


# ---------------------------------------------------------------------------
# Health / Status
# ---------------------------------------------------------------------------

class HealthStatus(BaseModel):
    """Response model for the /health endpoint."""
    status: str = Field(description="'ok' when the service is running normally")
    app_name: str
    version: str
    environment: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ---------------------------------------------------------------------------
# User roles (used across dashboard routing)
# ---------------------------------------------------------------------------

class UserRole(str):
    """Enumeration of user roles in the system."""
    CITIZEN = "citizen"
    CLEANER = "cleaner"
    MUNICIPAL_STAFF = "municipal_staff"
    ADMIN = "admin"


# ---------------------------------------------------------------------------
# Placeholder models for future phases
# ---------------------------------------------------------------------------
# These stubs define the *shape* of data that future phases will populate.
# They keep the API contract stable while implementations are added later.

class WasteReport(BaseModel):
    """
    Represents a citizen-submitted waste complaint.
    Full implementation: Phase 2
    """
    # TODO: Phase 2 — add location, image_url, description, status fields
    pass


class CleanupTask(BaseModel):
    """
    Represents a task assigned to a cleaner.
    Full implementation: Phase 2
    """
    # TODO: Phase 2 — add assigned_complaint_id, cleaner_id, status, route fields
    pass


class RouteOptimizationResult(BaseModel):
    """
    Result returned by the route optimizer AI service.
    Full implementation: Phase 4
    """
    # TODO: Phase 4 — add ordered_locations, estimated_duration, distance_km fields
    pass
