"""
SwachhLoop AI — Database Session
==================================
Sets up the async SQLAlchemy engine and session factory.

Phase 1: The engine is configured and the session factory is ready.
         No models or migrations are created yet — those come in Phase 2.

Phase 2+: Run Alembic migrations to create tables, then use
          get_db() as a FastAPI dependency to inject sessions.

Requirements:
  - DATABASE_URL must be set in .env (see .env.example)
  - PostgreSQL must be running for actual DB operations
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from backend.core.config import settings


# ---------------------------------------------------------------------------
# Async engine
# ---------------------------------------------------------------------------
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,       # Log SQL statements in debug mode
    pool_pre_ping=True,        # Verify connections before use
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,    # Avoid lazy-load errors after commit
    autocommit=False,
    autoflush=False,
)

# ---------------------------------------------------------------------------
# Declarative base — all ORM models will inherit from this (Phase 2+)
# ---------------------------------------------------------------------------
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


# ---------------------------------------------------------------------------
# FastAPI dependency — yields a database session per request
# ---------------------------------------------------------------------------
async def get_db() -> AsyncSession:  # type: ignore[misc]
    """
    Dependency that provides a database session for a single request.

    Usage in a route:
        @router.get("/example")
        async def example(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
