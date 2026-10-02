"""
SwachhLoop AI — Database Persistence Across Restarts Test
===========================================================
Tests:
  Verifies that relational database records (users, complaints, tasks,
  notifications, audit logs) survive backend engine shutdown and restart.
"""

import os
import tempfile
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from backend.db.session import Base
from backend.models.user import User, UserRole
from backend.models.complaint import Complaint, ComplaintStatus, ComplaintPriority
from backend.models.task import CleaningTask, TaskStatus
from backend.models.audit_log import AuditLog
from backend.models.notification import Notification, NotificationType
from backend.repositories import user_repo, complaint_repo, task_repo, audit_log_repo, notification_repo
from backend.services.auth_service import hash_password

pytestmark = pytest.mark.asyncio


async def test_database_persistence_across_restarts(tmp_path):
    """
    Simulates a backend server restart cycle:
      1. Boot engine 1 on a persistent SQLite file.
      2. Write users, complaint, task, notification, audit log.
      3. Terminate/dispose engine 1 (server shutdown).
      4. Boot engine 2 on the exact same SQLite file (server restart).
      5. Verify all data persists intact with correct relations.
    """
    db_file = tmp_path / "persistence_test.db"
    db_url = f"sqlite+aiosqlite:///{db_file}"

    # -------------------------------------------------------------------------
    # CYCLE 1: Server Startup & Initial Writes
    # -------------------------------------------------------------------------
    engine_1 = create_async_engine(db_url, poolclass=NullPool)
    session_factory_1 = async_sessionmaker(bind=engine_1, class_=AsyncSession, expire_on_commit=False)

    # Initialize schema
    async with engine_1.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory_1() as db:
        # Create Citizen
        citizen = await user_repo.create_user(
            db=db,
            email="citizen_persist@swachhloop.ai",
            hashed_password=hash_password("citizenpass123"),
            full_name="Persist Citizen",
            role=UserRole.CITIZEN,
            ward="Ward 5",
        )
        citizen_id = citizen.id

        # Create Cleaner
        cleaner = await user_repo.create_user(
            db=db,
            email="cleaner_persist@swachhloop.ai",
            hashed_password=hash_password("cleanerpass123"),
            full_name="Persist Cleaner",
            role=UserRole.CLEANER,
            employee_id="CLN-PERSIST",
        )
        cleaner_id = cleaner.id

        # Create Complaint
        complaint = await complaint_repo.create_complaint(
            db=db,
            citizen_id=citizen_id,
            title="Persisted Garbage Pile",
            description="Should survive restart",
            latitude=10.528,
            longitude=76.215,
            location_label="Main Junction",
            waste_type="Mixed Solid",
            priority=ComplaintPriority.HIGH,
        )
        complaint_id = complaint.id

        # Create Task
        task = await task_repo.create_task(
            db=db,
            complaint_id=complaint_id,
            assigned_to=cleaner_id,
            notes="Priority pickup",
        )
        task_id = task.id

        # Create Notification
        notif = await notification_repo.create_notification(
            db=db,
            user_id=cleaner_id,
            title="Task Assigned",
            message="Please clear garbage",
            type=NotificationType.INFO,
        )
        notif_id = notif.id

        # Create Audit Log
        await audit_log_repo.log_action(
            db=db,
            action="PERSISTENCE_TEST_INIT",
            actor_id=citizen_id,
            resource_type="complaint",
            resource_id=str(complaint_id),
            detail="Created for persistence test",
        )
        await db.commit()

    # Shutdown Cycle 1 (close connection & dispose engine)
    await engine_1.dispose()

    # -------------------------------------------------------------------------
    # CYCLE 2: Server Restart & Verification
    # -------------------------------------------------------------------------
    engine_2 = create_async_engine(db_url, poolclass=NullPool)
    session_factory_2 = async_sessionmaker(bind=engine_2, class_=AsyncSession, expire_on_commit=False)

    # Safe create_all on startup (matches init_db)
    async with engine_2.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory_2() as db:
        # Verify Citizen survived
        loaded_citizen = await user_repo.get_user_by_id(db, citizen_id)
        assert loaded_citizen is not None
        assert loaded_citizen.email == "citizen_persist@swachhloop.ai"
        assert loaded_citizen.full_name == "Persist Citizen"
        assert loaded_citizen.role == UserRole.CITIZEN

        # Verify Cleaner survived
        loaded_cleaner = await user_repo.get_user_by_id(db, cleaner_id)
        assert loaded_cleaner is not None
        assert loaded_cleaner.email == "cleaner_persist@swachhloop.ai"
        assert loaded_cleaner.employee_id == "CLN-PERSIST"

        # Verify Complaint survived with citizen relation
        loaded_complaint = await complaint_repo.get_complaint_by_id(db, complaint_id)
        assert loaded_complaint is not None
        assert loaded_complaint.title == "Persisted Garbage Pile"
        assert loaded_complaint.citizen_id == citizen_id
        assert loaded_complaint.citizen.full_name == "Persist Citizen"
        assert loaded_complaint.priority == ComplaintPriority.HIGH

        # Verify Task survived
        loaded_task = await task_repo.get_task_by_id(db, task_id)
        assert loaded_task is not None
        assert loaded_task.complaint_id == complaint_id
        assert loaded_task.assigned_to == cleaner_id
        assert loaded_task.status == TaskStatus.PENDING

        # Verify Notification survived
        notifications = await notification_repo.get_notifications_for_user(db, cleaner_id)
        assert len(notifications) == 1
        assert notifications[0].id == notif_id
        assert notifications[0].title == "Task Assigned"

        # Verify Audit Log survived
        logs = await audit_log_repo.get_audit_log(db)
        actions = [l.action for l in logs]
        assert "PERSISTENCE_TEST_INIT" in actions

        # Verify we can continue writing new data on the restored DB
        updated_task = await task_repo.update_task_status(db, task_id, TaskStatus.COMPLETED)
        assert updated_task.status == TaskStatus.COMPLETED
        await db.commit()

    await engine_2.dispose()
