"""
SwachhLoop AI — Frontend API Client (Phase 2 Mock Boundary)
============================================================
All data fetching for the frontend goes through this module.

Phase 2: Returns mock data from frontend/data/mock_data.py
Phase 3: Replace mock functions with real httpx calls to the FastAPI backend.

Example Phase 3 replacement:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{API_BASE_URL}/complaints")
        return response.json()

The function signatures should remain the same so page components
need minimal changes during Phase 3 integration.
"""

import os
from frontend.data.mock_data import (
    DEMO_USERS,
    MOCK_COMPLAINTS,
    MOCK_TASKS,
    MOCK_NOTIFICATIONS,
    MOCK_MAP_MARKERS,
    MOCK_AWARENESS_CONTENT,
    MOCK_USERS_ADMIN,
    MOCK_SYSTEM_HEALTH,
    MUNICIPAL_STATS,
    MOCK_AUDIT_LOG,
)

# ---------------------------------------------------------------------------
# Configuration
# Phase 3: Use this URL for real API calls.
# ---------------------------------------------------------------------------
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


# ---------------------------------------------------------------------------
# Authentication
# Phase 3: POST /auth/login → JWT token → store in session
# ---------------------------------------------------------------------------

def authenticate_user(email: str, password: str) -> dict | None:
    """
    Authenticate a user with email and password.

    Phase 2: Checks against DEMO_USERS list.
    Phase 3: POST {API_BASE_URL}/auth/login
    """
    for user in DEMO_USERS:
        if user["email"].lower() == email.lower() and user["password"] == password:
            return user
    return None


def get_demo_users() -> list[dict]:
    """Return demo user credentials for the login page helper."""
    return [
        {"email": u["email"], "role": u["role"], "name": u["name"]}
        for u in DEMO_USERS
    ]


# ---------------------------------------------------------------------------
# Complaints
# Phase 3: GET /complaints, POST /complaints, GET /complaints/{id}
# ---------------------------------------------------------------------------

def get_complaints(citizen_id: str | None = None) -> list[dict]:
    """
    Get complaints, optionally filtered by citizen.

    Phase 2: Returns filtered MOCK_COMPLAINTS.
    Phase 3: GET {API_BASE_URL}/complaints?citizen_id={citizen_id}
    """
    if citizen_id:
        return [c for c in MOCK_COMPLAINTS if c["citizen_id"] == citizen_id]
    return MOCK_COMPLAINTS


def get_complaint_by_id(complaint_id: str) -> dict | None:
    """
    Get a single complaint by ID.

    Phase 3: GET {API_BASE_URL}/complaints/{complaint_id}
    """
    for c in MOCK_COMPLAINTS:
        if c["id"] == complaint_id:
            return c
    return None


def submit_complaint(complaint_data: dict) -> dict:
    """
    Submit a new waste complaint.

    Phase 2: Returns a mock success response.
    Phase 3: POST {API_BASE_URL}/complaints (multipart form with image)
    """
    import random
    new_id = f"CMP-2024-{random.randint(900, 999):04d}"
    return {
        "success": True,
        "complaint_id": new_id,
        "status": "SUBMITTED",
        "message": "Report submitted successfully.",
    }


# ---------------------------------------------------------------------------
# Tasks (Cleaner)
# Phase 3: GET /tasks?cleaner_id={id}, PATCH /tasks/{id}
# ---------------------------------------------------------------------------

def get_tasks(cleaner_id: str | None = None) -> list[dict]:
    """
    Get tasks, optionally filtered by cleaner.

    Phase 3: GET {API_BASE_URL}/tasks?cleaner_id={cleaner_id}
    """
    return MOCK_TASKS


def get_task_by_id(task_id: str) -> dict | None:
    """
    Get a single task by ID.

    Phase 3: GET {API_BASE_URL}/tasks/{task_id}
    """
    for t in MOCK_TASKS:
        if t["id"] == task_id:
            return t
    return None


def update_task_status(task_id: str, status: str) -> dict:
    """
    Update a task status.

    Phase 2: Returns mock success.
    Phase 3: PATCH {API_BASE_URL}/tasks/{task_id} with {"status": status}
    """
    return {"success": True, "task_id": task_id, "new_status": status}


# ---------------------------------------------------------------------------
# Notifications
# Phase 3: GET /notifications?user_id={id}
# ---------------------------------------------------------------------------

def get_notifications(role: str) -> list[dict]:
    """
    Get notifications for a user role.

    Phase 3: GET {API_BASE_URL}/notifications?user_id={user_id}
    """
    return MOCK_NOTIFICATIONS.get(role, [])


# ---------------------------------------------------------------------------
# Map Data
# Phase 3: GET /complaints/map-markers
# ---------------------------------------------------------------------------

def get_map_markers(filter_type: str | None = None) -> list[dict]:
    """
    Get map markers for waste hotspots.

    Phase 3: GET {API_BASE_URL}/complaints/map-markers
    """
    if filter_type:
        return [m for m in MOCK_MAP_MARKERS if m["type"] == filter_type]
    return MOCK_MAP_MARKERS


# ---------------------------------------------------------------------------
# Awareness
# Phase 3: GET /awareness (RAG-powered content)
# ---------------------------------------------------------------------------

def get_awareness_content(language: str = "en") -> list[dict]:
    """
    Get awareness content/articles.

    Phase 3: GET {API_BASE_URL}/awareness?lang={language}
    (RAG pipeline will generate personalized content)
    """
    return MOCK_AWARENESS_CONTENT


# ---------------------------------------------------------------------------
# Admin
# Phase 3: GET /admin/users, GET /admin/health, GET /admin/audit-log
# ---------------------------------------------------------------------------

def get_all_users() -> list[dict]:
    """Phase 3: GET {API_BASE_URL}/admin/users"""
    return MOCK_USERS_ADMIN


def get_system_health() -> list[dict]:
    """Phase 3: GET {API_BASE_URL}/admin/health"""
    return MOCK_SYSTEM_HEALTH


def get_municipal_stats() -> dict:
    """Phase 3: GET {API_BASE_URL}/stats/municipal"""
    return MUNICIPAL_STATS


def get_audit_log() -> list[dict]:
    """Phase 3: GET {API_BASE_URL}/admin/audit-log"""
    return MOCK_AUDIT_LOG


# ---------------------------------------------------------------------------
# Backend Health Check (real — uses actual API)
# ---------------------------------------------------------------------------

def check_backend_health() -> dict:
    """
    Check if the backend API is reachable.
    This calls the REAL backend — not a mock.

    Phase 3: Already wired to real backend.
    """
    import httpx
    try:
        response = httpx.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return {"online": True, "data": response.json()}
        return {"online": False, "error": f"HTTP {response.status_code}"}
    except Exception as exc:
        return {"online": False, "error": str(exc)}
