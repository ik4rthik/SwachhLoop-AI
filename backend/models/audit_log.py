"""
SwachhLoop AI — AuditLog ORM Model
=====================================
Immutable append-only log of significant system actions.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.session import Base


class AuditLog(Base):
    """
    Records important actions for accountability and debugging.

    actor_id is nullable to support system-initiated actions
    (e.g., AI auto-validation, scheduled tasks).

    Relationship:
        actor — The user who performed the action (many:1, optional)
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Nullable: system/automated actions have no actor
    actor_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # What happened
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    # Examples: LOGIN | LOGOUT | REGISTER | SUBMIT_COMPLAINT | UPDATE_COMPLAINT_STATUS
    #           ASSIGN_TASK | UPDATE_TASK_STATUS | CREATE_USER | DEACTIVATE_USER

    # What it happened to
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Examples: complaint | task | user | system
    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Human-readable detail
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Network context
    ip_address: Mapped[str | None] = mapped_column(String(50), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    actor: Mapped["User | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates="audit_logs", foreign_keys=[actor_id]
    )

    def __repr__(self) -> str:
        return f"<AuditLog id={self.id} action={self.action!r} actor_id={self.actor_id}>"
