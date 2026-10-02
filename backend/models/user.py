"""
SwachhLoop AI — User ORM Model
================================
SQLAlchemy model for the users table.
"""

import enum
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.session import Base


class UserRole(str, enum.Enum):
    """Role enumeration — mirrors the four user roles across the platform."""
    CITIZEN = "citizen"
    CLEANER = "cleaner"
    MUNICIPAL_STAFF = "municipal_staff"
    ADMIN = "admin"


class User(Base):
    """
    Represents a registered user.

    Relationships:
        complaints      — Citizen's submitted complaints (1:many)
        assigned_tasks  — Cleaner's assigned cleaning tasks (1:many)
        notifications   — User's notifications (1:many)
        audit_logs      — Actions performed by this user (1:many)
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)

    # Optional profile fields
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ward: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employee_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    avatar_initials: Mapped[str | None] = mapped_column(String(10), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    complaints: Mapped[list["Complaint"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Complaint", back_populates="citizen", foreign_keys="Complaint.citizen_id"
    )
    assigned_tasks: Mapped[list["CleaningTask"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "CleaningTask", back_populates="assigned_cleaner", foreign_keys="CleaningTask.assigned_to"
    )
    notifications: Mapped[list["Notification"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Notification", back_populates="user"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "AuditLog", back_populates="actor", foreign_keys="AuditLog.actor_id"
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role}>"
