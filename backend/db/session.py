"""
SwachhLoop AI — Database Session
==================================
Sets up the async SQLAlchemy engine and session factory.

Supports:
  - SQLite (aiosqlite)  for local development
  - PostgreSQL (asyncpg) for staging/production

The driver is chosen automatically from DATABASE_URL:
  sqlite+aiosqlite:///./swachhloop.db     → local dev
  postgresql+asyncpg://user:pass@host/db  → production
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event

from backend.core.config import settings


# ---------------------------------------------------------------------------
# Async engine
# ---------------------------------------------------------------------------
# SQLite-specific connect_args (disable same-thread check for async use)
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,       # Log SQL statements in debug mode
    pool_pre_ping=True,        # Verify connections before use
    connect_args=connect_args,
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
# Declarative base — all ORM models will inherit from this
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
