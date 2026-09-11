"""
SwachhLoop AI — Health / Status Routes
========================================
Provides the /health and /status endpoints used by:
  - Load balancers to determine if the service is alive
  - Monitoring dashboards
  - The Streamlit frontend startup check
"""

from datetime import datetime

from fastapi import APIRouter

from backend.core.config import settings
from backend.models.schemas import HealthStatus

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthStatus,
    summary="Health check",
    description="Returns 200 OK with basic service information when the API is running.",
)
async def health_check() -> HealthStatus:
    """
    Lightweight health probe.
    Does NOT check database connectivity in Phase 1 — that comes in Phase 2
    once the DB layer is fully wired.
    """
    return HealthStatus(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.utcnow(),
    )


@router.get(
    "/status",
    summary="Detailed status",
    description="Returns extended service status including environment and debug flag.",
)
async def service_status() -> dict:
    """
    Extended status — useful during development to confirm env vars loaded correctly.
    Should be restricted/removed in production.
    """
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_env,
        "debug": settings.debug,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "api": "ok",
            "database": "not_checked",   # Phase 2: will ping DB
            "ai_services": "not_enabled", # Phase 3+
        },
    }
