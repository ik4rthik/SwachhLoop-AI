"""
SwachhLoop AI — User Repository
==================================
All database operations related to the users table.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User, UserRole


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.created_at))
    return list(result.scalars().all())


async def get_users_by_role(db: AsyncSession, role: UserRole) -> list[User]:
    result = await db.execute(select(User).where(User.role == role))
    return list(result.scalars().all())


async def create_user(
    db: AsyncSession,
    email: str,
    hashed_password: str,
    full_name: str,
    role: UserRole,
    phone: str | None = None,
    ward: str | None = None,
    employee_id: str | None = None,
    department: str | None = None,
    avatar_initials: str | None = None,
) -> User:
    """Insert a new user and return the persisted instance."""
    # Generate avatar initials from name if not provided
    if avatar_initials is None:
        parts = full_name.strip().split()
        avatar_initials = "".join(p[0].upper() for p in parts[:2])

    user = User(
        email=email.lower(),
        hashed_password=hashed_password,
        full_name=full_name,
        role=role,
        phone=phone,
        ward=ward,
        employee_id=employee_id,
        department=department,
        avatar_initials=avatar_initials,
        is_active=True,
    )
    db.add(user)
    await db.flush()  # Assigns PK without full commit
    await db.refresh(user)
    return user


async def update_user_active(db: AsyncSession, user_id: int, is_active: bool) -> User | None:
    user = await get_user_by_id(db, user_id)
    if user is None:
        return None
    user.is_active = is_active
    await db.flush()
    await db.refresh(user)
    return user
