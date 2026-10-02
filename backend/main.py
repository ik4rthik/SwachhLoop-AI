"""
SwachhLoop AI — FastAPI Application Entry Point
================================================
Phase 3: Full backend with authentication, database, and all API routes.

Run with:
    uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

Architecture:
    Streamlit Frontend
         ↓  HTTP
    FastAPI (this file)
         ↓
    backend/api/routes/   ← API route handlers
         ↓
    backend/services/     ← Business logic / AI service interfaces
         ↓
    backend/repositories/ ← Data access layer
         ↓
    backend/db/           ← Database session & ORM models
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.core.config import settings
from backend.api.routes import health
from backend.api.routes import auth, complaints, tasks, notifications, admin, stats

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    # --- STARTUP ---
    logger.info("=" * 60)
    logger.info(f"  {settings.app_name} v{settings.app_version}")
    logger.info(f"  Environment : {settings.app_env}")
    logger.info(f"  Debug mode  : {settings.debug}")
    logger.info(f"  Database    : {settings.database_url[:40]}...")
    logger.info(f"  Storage     : {settings.storage_backend}")
    logger.info(f"  Docs        : http://{settings.backend_host}:{settings.backend_port}/docs")
    logger.info("=" * 60)

    # Initialize database (create tables + seed demo users)
    from backend.db.init_db import init_db
    await init_db()
    logger.info("Database ready.")

    yield

    # --- SHUTDOWN ---
    logger.info(f"{settings.app_name} shutting down.")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "SwachhLoop AI — Autonomous Multi-Agent System for Closed-Loop "
        "Smart Civic Waste Management. Backend REST API.\n\n"
        "Phase 3: Real authentication, database, and full API."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        f"http://localhost:{settings.frontend_port}",
        "http://127.0.0.1:8501",
        f"http://127.0.0.1:{settings.frontend_port}",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global error handler — never expose internal details
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# ---------------------------------------------------------------------------
# Static files — serve uploaded images
# ---------------------------------------------------------------------------
import os
os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------

@app.get("/", tags=["root"], summary="API root")
async def root() -> dict:
    """Returns a brief welcome message and links to docs."""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": settings.app_version,
        "phase": "Phase 3 — Authentication + Database + Backend Integration",
        "docs": "/docs",
        "health": "/health",
    }


# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------

# Phase 1 — health (kept at root level, no prefix change)
app.include_router(health.router)

# Phase 3 — all new routes under /api prefix
app.include_router(auth.router,          prefix="/api/auth",          tags=["auth"])
app.include_router(complaints.router,    prefix="/api/complaints",    tags=["complaints"])
app.include_router(tasks.router,         prefix="/api/tasks",         tags=["tasks"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(admin.router,         prefix="/api/admin",         tags=["admin"])
app.include_router(stats.router,         prefix="/api/stats",         tags=["stats"])
