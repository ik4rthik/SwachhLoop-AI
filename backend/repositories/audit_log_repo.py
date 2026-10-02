"""
SwachhLoop AI — Audit Log Repository
=======================================
Append-only write operations for audit_logs.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.models.audit_log import AuditLog


async def log_action(
    db: AsyncSession,
    action: str,
    actor_id: int | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    detail: str | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Append an immutable audit log entry."""
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail,
        ip_address=ip_address,
    )
    db.add(entry)
    await db.flush()
    await db.refresh(entry)
    return entry


async def get_audit_log(
    db: AsyncSession,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    result = await db.execute(
        select(AuditLog)
        .options(selectinload(AuditLog.actor))
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())
