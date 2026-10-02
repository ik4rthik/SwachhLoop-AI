"""
SwachhLoop AI — Database Initialization
=========================================
Creates all tables and seeds demo users for local development.

Usage:
    python -m backend.db.init_db

Or called automatically during FastAPI startup in development mode.

Seeded demo users match the Phase 2 mock credentials so the frontend
demo quick-fill still works after Phase 3 backend integration.
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import engine, AsyncSessionLocal, Base
from backend.models import (  # noqa: F401  — registers all tables with Base.metadata
    User, UserRole, Complaint, CleaningTask, Notification, AuditLog
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Demo seed data  (matches Phase 2 mock_data.py DEMO_USERS)
# ---------------------------------------------------------------------------
DEMO_USERS = [
    {
        "email": "citizen@swachhloop.ai",
        "password": "demo123",
        "full_name": "Arjun Nair",
        "role": UserRole.CITIZEN,
        "phone": "+91 98765 43210",
        "ward": "Ward 7 — Thrissur",
        "avatar_initials": "AN",
    },
    {
        "email": "cleaner@swachhloop.ai",
        "password": "demo123",
        "full_name": "Rajan Pillai",
        "role": UserRole.CLEANER,
        "phone": "+91 87654 32109",
        "ward": "Zone B — Thrissur",
        "employee_id": "CLN-042",
        "avatar_initials": "RP",
    },
    {
        "email": "staff@swachhloop.ai",
        "password": "demo123",
        "full_name": "Priya Menon",
        "role": UserRole.MUNICIPAL_STAFF,
        "phone": "+91 76543 21098",
        "department": "Waste Management — Thrissur Corporation",
        "employee_id": "STAFF-011",
        "avatar_initials": "PM",
    },
    {
        "email": "admin@swachhloop.ai",
        "password": "demo123",
        "full_name": "Dr. Suresh Kumar",
        "role": UserRole.ADMIN,
        "phone": "+91 65432 10987",
        "department": "IT & System Administration",
        "employee_id": "ADMIN-001",
        "avatar_initials": "SK",
    },
]


async def create_tables() -> None:
    """Drop-safe table creation. Does not drop existing tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created (or already exist).")


async def seed_demo_users(db: AsyncSession) -> None:
    """
    Insert demo users if they do not already exist.
    Uses the same credentials as Phase 2 mock_data.py.
    """
    # Import here to avoid circular imports at module level
    from backend.services.auth_service import hash_password

    for user_data in DEMO_USERS:
        result = await db.execute(
            select(User).where(User.email == user_data["email"])
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            continue  # Already seeded

        user = User(
            email=user_data["email"],
            hashed_password=hash_password(user_data["password"]),
            full_name=user_data["full_name"],
            role=user_data["role"],
            phone=user_data.get("phone"),
            ward=user_data.get("ward"),
            employee_id=user_data.get("employee_id"),
            department=user_data.get("department"),
            avatar_initials=user_data.get("avatar_initials"),
            is_active=True,
        )
        db.add(user)
        logger.info(f"Seeding demo user: {user_data['email']} ({user_data['role'].value})")

    await db.commit()
    logger.info("Demo user seeding complete.")


async def init_db() -> None:
    """
    Full database initialization:
      1. Create all tables.
      2. Seed demo users.
    """
    await create_tables()
    async with AsyncSessionLocal() as db:
        await seed_demo_users(db)
    logger.info("Database initialization complete.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(init_db())
