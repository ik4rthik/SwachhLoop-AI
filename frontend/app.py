"""
SwachhLoop AI — Streamlit Application Entry Point
==================================================
Phase 2: Unified role-based frontend with glassmorphic design system.

Run with:
    streamlit run frontend/app.py

Architecture:
    app.py (this file)
        ├── Landing page (public)
        ├── Login page (shared for all roles)
        └── Role-based dashboards (session-state auth)
            ├── pages/citizen.py
            ├── pages/cleaner.py
            ├── pages/municipal_staff.py
            └── pages/admin.py

Authentication:
    Phase 2: Demo session-state auth (mock users).
    Phase 3: Replace authenticate_user() in services/api_client.py
             with real JWT authentication against the FastAPI backend.

Navigation:
    Session state keys:
        current_page_root : "landing" | "login" | "app"
        logged_in         : bool
        user              : dict (logged-in user data)
        role              : str ("citizen" | "cleaner" | "municipal_staff" | "admin")
        current_page      : str (sub-page within the role app)
        selected_complaint: str (complaint ID for detail view)
        selected_task     : str (task ID for detail view)
        report_success    : bool (flag for report waste success state)

Backend compatibility:
    The FastAPI backend (backend/main.py) is completely unchanged.
    Phase 1 endpoints (/health, /status) remain fully functional.
    The Admin dashboard's real health check button still calls the live API.
"""

import sys
import os

# ── Ensure project root is on sys.path so 'frontend.*' imports work ──────────
# Streamlit runs scripts directly and may not include the project root.
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import streamlit as st

# ── Page config — MUST be the first Streamlit call ──────────────────────────
st.set_page_config(
    page_title="SwachhLoop AI",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="auto",
)

# ── Inject design system CSS ─────────────────────────────────────────────────
from frontend.components.design_system import inject_css
inject_css()

# ── Session state initialisation ─────────────────────────────────────────────
if "current_page_root" not in st.session_state:
    st.session_state["current_page_root"] = "landing"
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# ── Root-level routing ───────────────────────────────────────────────────────
root_page = st.session_state.get("current_page_root", "landing")

# Redirect to login if "goto_login" was set
if st.session_state.pop("goto_login", False):
    root_page = "login"
    st.session_state["current_page_root"] = "login"

# If logged in, always route to app (unless explicitly logging out resets state)
if st.session_state.get("logged_in") and root_page not in ("app",):
    root_page = "app"
    st.session_state["current_page_root"] = "app"

# ── Landing page ─────────────────────────────────────────────────────────────
if root_page == "landing":
    # No sidebar on landing
    st.markdown(
        """<style>[data-testid="stSidebar"]{display:none;}</style>""",
        unsafe_allow_html=True,
    )
    from frontend.pages import landing
    landing.render()


# ── Login page ────────────────────────────────────────────────────────────────
elif root_page == "login":
    st.markdown(
        """<style>[data-testid="stSidebar"]{display:none;}</style>""",
        unsafe_allow_html=True,
    )
    from frontend.pages import login
    login.render()

# ── Main application (authenticated) ─────────────────────────────────────────
elif root_page == "app":
    if not st.session_state.get("logged_in"):
        # Not authenticated → send to login
        st.session_state["current_page_root"] = "login"
        st.rerun()

    role = st.session_state.get("role", "citizen")
    user = st.session_state.get("user", {})

    # Render role-aware sidebar
    from frontend.components.layout import render_sidebar
    render_sidebar(role, user)

    # Route to the appropriate role module
    if role == "citizen":
        from frontend.pages import citizen
        citizen.render()

    elif role == "cleaner":
        from frontend.pages import cleaner
        cleaner.render()

    elif role == "municipal_staff":
        from frontend.pages import municipal_staff
        municipal_staff.render()

    elif role == "admin":
        from frontend.pages import admin
        admin.render()

    else:
        st.error(f"Unknown role: {role}. Please log out and sign in again.")
        if st.button("🔐 Sign In Again"):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

# ── Fallback ─────────────────────────────────────────────────────────────────
else:
    st.session_state["current_page_root"] = "landing"
    st.rerun()
