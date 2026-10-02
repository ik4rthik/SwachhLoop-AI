"""
SwachhLoop AI — Frontend API Client (Phase 3)
==============================================
All data fetching for the frontend goes through this module.

Phase 3: Real httpx calls to the FastAPI backend.
         Mock data fallback preserved for demo/offline mode.

IMPORTANT: Streamlit is synchronous. All API calls use httpx sync client.

Authentication:
    Token stored in st.session_state["access_token"]
    All authenticated calls pass Authorization: Bearer {token}

Error handling:
    - 401 → session cleared → redirected to login
    - 403 → access denied message shown
    - 404 → None returned
    - Other errors → fallback to mock data with warning shown
"""

import os
import logging
from typing import Any

import httpx
import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
_TIMEOUT = 10.0  # seconds

# ---------------------------------------------------------------------------
# Fallback mock data (for demo mode / offline / unavailable backend)
# ---------------------------------------------------------------------------
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
# Internal helpers
# ---------------------------------------------------------------------------

def _get_token() -> str | None:
    """Return the JWT token from Streamlit session state."""
    return st.session_state.get("access_token")


def _auth_headers() -> dict[str, str]:
    """Build Authorization header dict."""
    token = _get_token()
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _handle_401() -> None:
    """Clear session and trigger redirect to login."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.session_state["current_page_root"] = "login"
    st.warning("Your session has expired. Please sign in again.")
    st.rerun()


def _api_get(path: str, params: dict | None = None) -> Any | None:
    """
    Perform a GET request to the backend API.
    Returns parsed JSON or None on error.
    """
    try:
        resp = httpx.get(
            f"{API_BASE_URL}{path}",
            headers=_auth_headers(),
            params=params,
            timeout=_TIMEOUT,
        )
        if resp.status_code == 401:
            _handle_401()
            return None
        if resp.status_code == 403:
            st.error("Access denied. You do not have permission for this action.")
            return None
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        logger.warning(f"Backend unreachable at {API_BASE_URL}. Using mock data.")
        return None
    except Exception as exc:
        logger.error(f"API GET {path} failed: {exc}")
        return None


def _api_post(path: str, json: dict | None = None, data: dict | None = None, files: dict | None = None) -> Any | None:
    """Perform a POST request to the backend API."""
    try:
        resp = httpx.post(
            f"{API_BASE_URL}{path}",
            headers=_auth_headers(),
            json=json,
            data=data,
            files=files,
            timeout=_TIMEOUT,
        )
        if resp.status_code == 401:
            _handle_401()
            return None
        if resp.status_code == 403:
            st.error("Access denied.")
            return None
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        logger.warning(f"Backend unreachable at {API_BASE_URL}.")
        return None
    except Exception as exc:
        logger.error(f"API POST {path} failed: {exc}")
        return None


def _api_patch(path: str, json: dict | None = None, params: dict | None = None) -> Any | None:
    """Perform a PATCH request to the backend API."""
    try:
        resp = httpx.patch(
            f"{API_BASE_URL}{path}",
            headers=_auth_headers(),
            json=json,
            params=params,
            timeout=_TIMEOUT,
        )
        if resp.status_code == 401:
            _handle_401()
            return None
        if resp.status_code == 403:
            st.error("Access denied.")
            return None
        resp.raise_for_status()
        return resp.json()
    except httpx.ConnectError:
        logger.warning(f"Backend unreachable at {API_BASE_URL}.")
        return None
    except Exception as exc:
        logger.error(f"API PATCH {path} failed: {exc}")
        return None


def _is_backend_up() -> bool:
    """Quick check whether backend is reachable."""
    try:
        resp = httpx.get(f"{API_BASE_URL}/health", timeout=3.0)
        return resp.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

def authenticate_user(email: str, password: str) -> dict | None:
    """
    Authenticate against the real backend.
    Falls back to mock DEMO_USERS if backend is unreachable.

    Returns the user dict (compatible with Phase 2 session state format)
    and stores the JWT token in st.session_state["access_token"].
    """
    if not _is_backend_up():
        # Offline fallback — Phase 2 demo mode
        for user in DEMO_USERS:
            if user["email"].lower() == email.lower() and user["password"] == password:
                st.session_state["access_token"] = None  # No real token in demo mode
                st.session_state["demo_mode"] = True
                return user
        return None

    result = _api_post("/api/auth/login", json={"email": email, "password": password})
    if result is None:
        return None

    token = result.get("access_token")
    user_data = result.get("user", {})

    if not token or not user_data:
        return None

    # Store token for subsequent requests
    st.session_state["access_token"] = token
    st.session_state["demo_mode"] = False

    # Normalize API response to match Phase 2 session state format
    return _normalize_user(user_data)


def _normalize_user(api_user: dict) -> dict:
    """
    Convert API UserResponse to the dict format Phase 2 pages expect.
    Preserves all fields pages use (id, name, email, role, avatar_initials, ward, etc.)
    """
    return {
        "id": str(api_user.get("id", "")),  # Pages use string IDs
        "name": api_user.get("full_name", ""),
        "email": api_user.get("email", ""),
        "role": api_user.get("role", "citizen"),
        "avatar_initials": api_user.get("avatar_initials") or _make_initials(api_user.get("full_name", "")),
        "ward": api_user.get("ward"),
        "phone": api_user.get("phone"),
        "joined": "—",  # Not returned by API; could add created_at formatting
        "employee_id": api_user.get("employee_id"),
        "department": api_user.get("department"),
        # Citizen-specific defaults (populated from complaints count in Phase 4)
        "total_reports": 0,
        "resolved": 0,
        # Cleaner-specific defaults
        "tasks_completed": 0,
    }


def _make_initials(name: str) -> str:
    parts = name.strip().split()
    return "".join(p[0].upper() for p in parts[:2]) if parts else "?"


def get_demo_users() -> list[dict]:
    """Return demo user credentials for the login page quick-fill."""
    return [{"email": u["email"], "role": u["role"], "name": u["name"]} for u in DEMO_USERS]


# ---------------------------------------------------------------------------
# Complaints
# ---------------------------------------------------------------------------

def get_complaints(citizen_id: str | None = None) -> list[dict]:
    """
    Fetch complaints from the real API.
    Falls back to mock if backend unavailable.
    """
    params = {}
    if citizen_id:
        params["citizen_id"] = citizen_id  # Ignored server-side for citizens (JWT enforces it)

    result = _api_get("/api/complaints", params=params if not citizen_id else None)
    if result is None:
        # Fallback
        if citizen_id:
            return [c for c in MOCK_COMPLAINTS if c.get("citizen_id") == citizen_id]
        return MOCK_COMPLAINTS

    return [_normalize_complaint(c) for c in result]


def get_complaint_by_id(complaint_id: str) -> dict | None:
    result = _api_get(f"/api/complaints/{complaint_id}")
    if result is None:
        # Fallback
        for c in MOCK_COMPLAINTS:
            if c["id"] == complaint_id:
                return c
        return None
    return _normalize_complaint(result)


def submit_complaint(complaint_data: dict) -> dict:
    """
    Submit a new waste complaint.
    complaint_data may contain: title, description, latitude, longitude,
    location_label, waste_type, priority, image (bytes or None).
    """
    form_data = {
        k: str(v) for k, v in complaint_data.items()
        if k != "image" and v is not None
    }

    files = None
    image = complaint_data.get("image")
    if image is not None:
        if isinstance(image, bytes):
            files = {"image": ("waste_image.jpg", image, "image/jpeg")}
        elif hasattr(image, "read"):
            files = {"image": (getattr(image, "name", "upload.jpg"), image.read(), "image/jpeg")}

    if files:
        result = _api_post("/api/complaints", data=form_data, files=files)
    else:
        result = _api_post("/api/complaints", data=form_data)

    if result is None:
        import random
        return {
            "success": True,
            "complaint_id": f"CMP-DEMO-{random.randint(900, 999):04d}",
            "status": "SUBMITTED",
            "message": "Report submitted (demo mode — backend unavailable).",
        }

    return {
        "success": True,
        "complaint_id": str(result.get("id", "?")),
        "status": result.get("status", "SUBMITTED"),
        "message": "Report submitted successfully.",
    }


def _normalize_complaint(api_complaint: dict) -> dict:
    """Normalize API complaint response to Phase 2 mock format."""
    citizen = api_complaint.get("citizen") or {}
    return {
        "id": str(api_complaint.get("id", "")),
        "citizen_id": str(api_complaint.get("citizen_id", "")),
        "citizen_name": citizen.get("full_name", "—"),
        "title": api_complaint.get("title") or "Untitled Complaint",
        "description": api_complaint.get("description", ""),
        "waste_type": api_complaint.get("waste_type", "Unknown"),
        "location": api_complaint.get("location_label", "—"),
        "lat": api_complaint.get("latitude"),
        "lon": api_complaint.get("longitude"),
        "priority": api_complaint.get("priority", "MEDIUM"),
        "status": api_complaint.get("status", "SUBMITTED"),
        "reported_at": _fmt_datetime(api_complaint.get("reported_at", "")),
        "image_url": api_complaint.get("image_url"),
        "ai_confidence": int((api_complaint.get("waste_confidence") or 0) * 100) or None,
        "ai_reason": "AI analysis pending (Phase 4).",
        "assigned_cleaner": None,
        "timeline": _build_timeline(api_complaint.get("status", "SUBMITTED")),
    }


def _fmt_datetime(dt_str: str) -> str:
    if not dt_str:
        return "—"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except Exception:
        return dt_str[:16] if len(dt_str) > 16 else dt_str


_STATUS_ORDER = ["SUBMITTED", "VALIDATED", "ASSIGNED", "CLEANING", "VERIFICATION", "RESOLVED"]


def _build_timeline(current_status: str) -> list[dict]:
    try:
        idx = _STATUS_ORDER.index(current_status)
    except ValueError:
        idx = 0
    return [
        {"step": s, "done": i <= idx, "time": None}
        for i, s in enumerate(_STATUS_ORDER)
    ]


# ---------------------------------------------------------------------------
# Tasks (Cleaner)
# ---------------------------------------------------------------------------

def get_tasks(cleaner_id: str | None = None) -> list[dict]:
    result = _api_get("/api/tasks")
    if result is None:
        return MOCK_TASKS
    return [_normalize_task(t) for t in result]


def get_task_by_id(task_id: str) -> dict | None:
    result = _api_get(f"/api/tasks/{task_id}")
    if result is None:
        for t in MOCK_TASKS:
            if t["id"] == task_id:
                return t
        return None
    return _normalize_task(result)


def update_task_status(task_id: str, status: str) -> dict:
    result = _api_patch(f"/api/tasks/{task_id}", json={"status": status})
    if result is None:
        return {"success": True, "task_id": task_id, "new_status": status}
    return {"success": True, "task_id": str(result.get("id")), "new_status": result.get("status")}


def _normalize_task(api_task: dict) -> dict:
    return {
        "id": str(api_task.get("id", "")),
        "complaint_id": str(api_task.get("complaint_id", "")),
        "title": api_task.get("complaint_title") or f"Task #{api_task.get('id', '?')}",
        "waste_type": api_task.get("complaint_waste_type", "Unknown"),
        "location": api_task.get("complaint_location", "—"),
        "lat": api_task.get("complaint_latitude"),
        "lon": api_task.get("complaint_longitude"),
        "priority": api_task.get("complaint_priority", "MEDIUM"),
        "distance": api_task.get("distance", "—"),
        "estimated_time": api_task.get("estimated_time", "—"),
        "reported_at": _fmt_datetime(api_task.get("created_at", "")),
        "assigned_at": _fmt_datetime(api_task.get("assigned_at", "")),
        "status": api_task.get("status", "PENDING"),
        "description": api_task.get("notes", ""),
        "image_url": api_task.get("before_image_url"),
        "after_image_url": api_task.get("after_image_url"),
    }


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

def get_notifications(role: str) -> list[dict]:
    """
    Fetch notifications for the current user.
    The role parameter is kept for API compatibility but JWT determines the user.
    """
    result = _api_get("/api/notifications")
    if result is None:
        return MOCK_NOTIFICATIONS.get(role, [])
    return [_normalize_notification(n) for n in result]


def _normalize_notification(api_notif: dict) -> dict:
    return {
        "id": str(api_notif.get("id", "")),
        "type": api_notif.get("type", "info"),
        "title": api_notif.get("title", ""),
        "message": api_notif.get("message", ""),
        "time": _fmt_datetime(api_notif.get("created_at", "")),
        "read": api_notif.get("is_read", False),
    }


# ---------------------------------------------------------------------------
# Map Data
# ---------------------------------------------------------------------------

def get_map_markers(filter_type: str | None = None) -> list[dict]:
    result = _api_get("/api/complaints/map-markers")
    if result is None:
        if filter_type:
            return [m for m in MOCK_MAP_MARKERS if m["type"] == filter_type]
        return MOCK_MAP_MARKERS

    markers = [
        {
            "id": str(m.get("id", "")),
            "lat": m.get("lat"),
            "lon": m.get("lon"),
            "type": m.get("type", "MEDIUM"),
            "label": m.get("label", ""),
            "complaint_id": str(m.get("complaint_id", "")),
        }
        for m in result
    ]
    if filter_type:
        markers = [m for m in markers if m["type"] == filter_type]
    return markers


# ---------------------------------------------------------------------------
# Awareness (static for now — Phase 4 will add RAG)
# ---------------------------------------------------------------------------

def get_awareness_content(language: str = "en") -> list[dict]:
    """Awareness content is static for Phase 3. RAG pipeline comes in Phase 4."""
    return MOCK_AWARENESS_CONTENT


# ---------------------------------------------------------------------------
# Admin
# ---------------------------------------------------------------------------

def get_all_users() -> list[dict]:
    result = _api_get("/api/admin/users")
    if result is None:
        return MOCK_USERS_ADMIN
    return [_normalize_admin_user(u) for u in result]


def _normalize_admin_user(api_user: dict) -> dict:
    role_display = {
        "citizen": "Citizen",
        "cleaner": "Cleaner",
        "municipal_staff": "Municipal Staff",
        "admin": "Admin",
    }
    return {
        "id": str(api_user.get("id", "")),
        "name": api_user.get("full_name", ""),
        "email": api_user.get("email", ""),
        "role": role_display.get(api_user.get("role", ""), api_user.get("role", "")),
        "ward": api_user.get("ward") or "—",
        "status": "Active" if api_user.get("is_active", True) else "Inactive",
        "joined": _fmt_datetime(api_user.get("created_at", "")),
    }


def get_system_health() -> list[dict]:
    result = _api_get("/api/admin/health")
    if result is None:
        return MOCK_SYSTEM_HEALTH
    return result


def get_municipal_stats() -> dict:
    result = _api_get("/api/stats/municipal")
    if result is None:
        return MUNICIPAL_STATS
    return result


def get_audit_log() -> list[dict]:
    result = _api_get("/api/admin/audit-log")
    if result is None:
        return MOCK_AUDIT_LOG
    return [_normalize_audit(e) for e in result]


def _normalize_audit(entry: dict) -> dict:
    actor = entry.get("actor_name") or "System"
    return {
        "time": _fmt_datetime(entry.get("created_at", "")),
        "user": actor,
        "action": entry.get("detail") or entry.get("action", ""),
        "type": entry.get("action", ""),
    }


# ---------------------------------------------------------------------------
# Backend Health Check (real — always calls actual backend)
# ---------------------------------------------------------------------------

def check_backend_health() -> dict:
    """Check if the backend API is reachable."""
    try:
        response = httpx.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return {"online": True, "data": response.json()}
        return {"online": False, "error": f"HTTP {response.status_code}"}
    except Exception as exc:
        return {"online": False, "error": str(exc)}
