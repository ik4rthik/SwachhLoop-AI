"""
SwachhLoop AI — Complaint ORM Model
=====================================
SQLAlchemy model for the complaints table.
"""

import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.session import Base


class ComplaintStatus(str, enum.Enum):
    """Lifecycle stages of a waste complaint."""
    SUBMITTED = "SUBMITTED"
    VALIDATED = "VALIDATED"
    ASSIGNED = "ASSIGNED"
    CLEANING = "CLEANING"
    VERIFICATION = "VERIFICATION"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"


class ComplaintPriority(str, enum.Enum):
    """Priority levels assessed for a complaint."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Complaint(Base):
    """
    Represents a citizen-submitted waste complaint.

    Relationships:
        citizen  — The user who submitted the complaint (many:1)
        task     — The associated cleaning task, if assigned (1:1)
    """
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    citizen_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Location
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_label: Mapped[str | None] = mapped_column(String(300), nullable=True)

    # Timestamps
    reported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Status & priority
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus), default=ComplaintStatus.SUBMITTED, nullable=False
    )
    priority: Mapped[ComplaintPriority] = mapped_column(
        Enum(ComplaintPriority), default=ComplaintPriority.MEDIUM, nullable=False
    )

    # Waste classification (AI placeholder fields)
    waste_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    waste_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    # User-submitted details
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    citizen: Mapped["User"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "User", back_populates="complaints", foreign_keys=[citizen_id]
    )
    task: Mapped["CleaningTask | None"] = relationship(  # type: ignore[name-defined]  # noqa: F821
        "CleaningTask", back_populates="complaint", uselist=False
    )

    def __repr__(self) -> str:
        return f"<Complaint id={self.id} status={self.status} priority={self.priority}>"
