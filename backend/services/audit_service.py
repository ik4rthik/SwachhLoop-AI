"""
SwachhLoop AI — Audit Service
================================
Convenience wrapper around audit_log_repo.
Routes call log_event() to record important actions without
repeating boilerplate.

Defined action constants ensure consistency across the codebase.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from backend.repositories.audit_log_repo import log_action

# ---------------------------------------------------------------------------
# Action constant strings
# ---------------------------------------------------------------------------
ACTION_LOGIN = "LOGIN"
ACTION_REGISTER = "REGISTER"
ACTION_SUBMIT_COMPLAINT = "SUBMIT_COMPLAINT"
ACTION_UPDATE_COMPLAINT_STATUS = "UPDATE_COMPLAINT_STATUS"
ACTION_ASSIGN_TASK = "ASSIGN_TASK"
ACTION_UPDATE_TASK_STATUS = "UPDATE_TASK_STATUS"
ACTION_CREATE_USER = "CREATE_USER"
ACTION_DEACTIVATE_USER = "DEACTIVATE_USER"
ACTION_REACTIVATE_USER = "REACTIVATE_USER"
ACTION_UPLOAD_EVIDENCE = "UPLOAD_EVIDENCE"


async def log_event(
    db: AsyncSession,
    action: str,
    actor_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
) -> None:
    """
    Write an audit log entry.
    Failures are logged but never raise — audit logging must not break user flows.
    """
    try:
        await log_action(
            db=db,
            action=action,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            ip_address=ip_address,
        )
    except Exception as exc:  # pragma: no cover
        import logging
        logging.getLogger(__name__).error(f"Audit log write failed: {exc}")
