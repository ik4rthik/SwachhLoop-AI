"""
SwachhLoop AI — Models Package
================================
Import all ORM models here so SQLAlchemy's Base.metadata knows about
every table when create_all() is called in db/init_db.py.

Import order matters for foreign key resolution:
  User → Complaint → CleaningTask → Notification → AuditLog
"""

from backend.models.user import User, UserRole  # noqa: F401
from backend.models.complaint import Complaint, ComplaintStatus, ComplaintPriority  # noqa: F401
from backend.models.task import CleaningTask, TaskStatus  # noqa: F401
from backend.models.notification import Notification, NotificationType  # noqa: F401
from backend.models.audit_log import AuditLog  # noqa: F401

__all__ = [
    "User",
    "UserRole",
    "Complaint",
    "ComplaintStatus",
    "ComplaintPriority",
    "CleaningTask",
    "TaskStatus",
    "Notification",
    "NotificationType",
    "AuditLog",
]
