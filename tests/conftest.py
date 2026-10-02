"""
SwachhLoop AI — Test Configuration
=====================================
Shared fixtures for all Phase 3 tests.

Uses an in-memory SQLite database so tests are:
  - Fast (no disk I/O)
  - Isolated (fresh DB per test session)
  - Independent of any real database
"""

import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from sqlalchemy.pool import StaticPool

from backend.db.session import Base, get_db
from backend.main import app
from backend.models import User, UserRole  # noqa: F401 — registers models with Base
from backend.services.auth_service import hash_password

# ---------------------------------------------------------------------------
# In-memory SQLite engine for tests
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# ---------------------------------------------------------------------------
# Session fixture — creates tables once, yields a session per test
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture(scope="function")
async def setup_database():
    """Create all tables fresh before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session(setup_database) -> AsyncSession:
    """Yield a fresh DB session, rolling back after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


# ---------------------------------------------------------------------------
# Override FastAPI's get_db dependency
# ---------------------------------------------------------------------------

async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


# ---------------------------------------------------------------------------
# HTTP test client
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def client(setup_database) -> AsyncClient:
    """Async HTTPX client wired to the FastAPI app (no real server needed)."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# Pre-seeded users
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def citizen_user(db_session: AsyncSession) -> User:
    from backend.repositories.user_repo import create_user
    user = await create_user(
        db=db_session,
        email="test_citizen@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test Citizen",
        role=UserRole.CITIZEN,
        ward="Test Ward",
    )
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def cleaner_user(db_session: AsyncSession) -> User:
    from backend.repositories.user_repo import create_user
    user = await create_user(
        db=db_session,
        email="test_cleaner@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test Cleaner",
        role=UserRole.CLEANER,
        employee_id="CLN-TEST",
    )
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def staff_user(db_session: AsyncSession) -> User:
    from backend.repositories.user_repo import create_user
    user = await create_user(
        db=db_session,
        email="test_staff@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test Staff",
        role=UserRole.MUNICIPAL_STAFF,
    )
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    from backend.repositories.user_repo import create_user
    user = await create_user(
        db=db_session,
        email="test_admin@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test Admin",
        role=UserRole.ADMIN,
    )
    await db_session.commit()
    return user



# ---------------------------------------------------------------------------
# Auth token helpers
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def citizen_token(client: AsyncClient, citizen_user: User) -> str:
    """Register then login to get a citizen JWT token."""
    resp = await client.post("/api/auth/login", json={
        "email": citizen_user.email,
        "password": "testpass123",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def cleaner_token(client: AsyncClient, cleaner_user: User) -> str:
    resp = await client.post("/api/auth/login", json={
        "email": cleaner_user.email,
        "password": "testpass123",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def staff_token(client: AsyncClient, staff_user: User) -> str:
    resp = await client.post("/api/auth/login", json={
        "email": staff_user.email,
        "password": "testpass123",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient, admin_user: User) -> str:
    resp = await client.post("/api/auth/login", json={
        "email": admin_user.email,
        "password": "testpass123",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]
