"""
SwachhLoop AI — FastAPI Application Entry Point
================================================
This is the root of the backend application.

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
    backend/db/           ← Database session & ORM models
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.api.routes import health

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "SwachhLoop AI — Autonomous Multi-Agent System for Closed-Loop "
        "Smart Civic Waste Management. Backend REST API."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# ---------------------------------------------------------------------------
# CORS middleware
# Allow the Streamlit frontend to call the API during local development.
# Tighten these origins for staging/production in Phase 2+.
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",      # Streamlit default port
        f"http://localhost:{settings.frontend_port}",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Startup / Shutdown lifecycle events
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def on_startup() -> None:
    """Runs once when the server starts."""
    logger.info("=" * 60)
    logger.info(f"  {settings.app_name} v{settings.app_version}")
    logger.info(f"  Environment : {settings.app_env}")
    logger.info(f"  Debug mode  : {settings.debug}")
    logger.info(f"  Docs        : http://{settings.backend_host}:{settings.backend_port}/docs")
    logger.info("=" * 60)
    # Phase 2: add DB connection check here
    # Phase 3: initialise AI service clients here


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """Runs once when the server shuts down."""
    logger.info(f"{settings.app_name} shutting down.")
    # Phase 2: close DB connection pool here


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------

@app.get("/", tags=["root"], summary="API root")
async def root() -> dict:
    """Returns a brief welcome message and links to docs."""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


# ---------------------------------------------------------------------------
# Register routers
# ---------------------------------------------------------------------------
app.include_router(health.router)

# Phase 2+ — uncomment as each feature is implemented:
# from backend.api.routes import auth, complaints, cleaners, admin
# app.include_router(auth.router,        prefix="/auth",       tags=["auth"])
# app.include_router(complaints.router,  prefix="/complaints", tags=["complaints"])
# app.include_router(cleaners.router,    prefix="/cleaners",   tags=["cleaners"])
# app.include_router(admin.router,       prefix="/admin",      tags=["admin"])
