"""
SwachhLoop AI — CleaningTask ORM Model
========================================
SQLAlchemy model for the cleaning_tasks table.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.session import Base


class TaskStatus(str, enum.Enum):
    """Lifecycle stages of a cleaning task."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class CleaningTask(Base):
    """
    A cleanup task assigned to a cleaner in response to a complaint.

    Relationships:
        complaint        — The source complaint (many:1)
        assigned_cleaner — The cleaner assigned to this task (many:1)
        assigning_staff  — The staff member who assigned it (many:1)
    """
    __tablename__ = "cleaning_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    complaint_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_to: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    assigned_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING, nullable=False
    )

    # Optional logistics metadata
    estimated_time: Mapped[str | None] = mapped_column(String(50), nullable=True)
    distance: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Cleanup evidence images (Phase 3+)
    before_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    after_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Timestamps
    assigned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    complaint: Mapped["Complaint"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "Complaint", back_populates="task", foreign_keys=[complaint_id]
    )
    assigned_cleaner: Mapped["User | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates="assigned_tasks", foreign_keys=[assigned_to]
    )
    assigning_staff: Mapped["User | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", foreign_keys=[assigned_by]
    )

    def __repr__(self) -> str:
        return f"<CleaningTask id={self.id} complaint_id={self.complaint_id} status={self.status}>"
