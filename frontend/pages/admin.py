"""
SwachhLoop AI — Admin Dashboard & Sub-pages
============================================
Phase 2: Full prototype admin interface.
Phase 3: Connect to real API + AI monitoring endpoints.

Sub-pages:
    dashboard     — System overview, user counts, health
    users         — User management table
    ai_monitoring — AI service status (Phase 3 stubs)
    knowledge_base — RAG knowledge base (Phase 3 stubs)
    audit_logs    — Action history
    settings      — System settings
"""

import streamlit as st
import os

from frontend.components import (
    render_topbar, stat_card, render_notifications,
)
from frontend.services.api_client import (
    get_all_users, get_system_health, get_audit_log,
    get_notifications, check_backend_health,
)


def render() -> None:
    user = st.session_state.get("user", {})
    current_page = st.session_state.get("current_page", "dashboard")

    render_topbar(user, "admin", current_page.replace("_", " ").title())

    if current_page == "dashboard":
        _render_dashboard(user)
    elif current_page == "users":
        _render_users()
    elif current_page == "ai_monitoring":
        _render_ai_monitoring()
    elif current_page == "knowledge_base":
        _render_knowledge_base()
    elif current_page == "audit_logs":
        _render_audit_logs()
    elif current_page == "settings":
        _render_settings()
    else:
        _render_dashboard(user)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def _render_dashboard(user: dict) -> None:
    all_users = get_all_users()

    citizens = [u for u in all_users if u["role"] == "Citizen"]
    cleaners = [u for u in all_users if u["role"] == "Cleaner"]
    staff = [u for u in all_users if u["role"] == "Municipal Staff"]
    admins = [u for u in all_users if u["role"] == "Admin"]
    active_users = [u for u in all_users if u["status"] == "Active"]

    st.markdown(
        f"""
        <div class="glass-card" style="padding:1.25rem 1.5rem;margin-bottom:1.25rem;">
            <div class="page-title">Admin Dashboard</div>
            <p class="page-subtitle">System health, user management, and platform oversight.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # User stats
    st.markdown('<div class="section-title">👥 User Overview</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1: stat_card("Total Users", len(all_users), "👥", "brand")
    with c2: stat_card("Citizens", len(citizens), "🏠", "default")
    with c3: stat_card("Cleaners", len(cleaners), "🧹", "default")
    with c4: stat_card("Municipal Staff", len(staff), "🏛️", "default")
    with c5: stat_card("Admins", len(admins), "⚙️", "default")

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1, 1])

    with left:
        st.markdown('<div class="section-title">🔧 System Health</div>', unsafe_allow_html=True)
        health_data = get_system_health()
        for svc in health_data:
            status_color = {"🟢": "#2d6a4f", "🟡": "#e65100", "🔴": "#c62828"}.get(svc["icon"], "#9090a8")
            st.markdown(
                f"""
                <div class="complaint-card" style="padding:0.75rem 1rem;">
                    <div style="display:flex;justify-content:space-between;align-items:center;">
                        <div style="display:flex;align-items:center;gap:0.6rem;">
                            <span style="font-size:1.1rem;">{svc['icon']}</span>
                            <div>
                                <div style="font-weight:600;font-size:0.88rem;">{svc['service']}</div>
                                <div style="font-size:0.75rem;color:var(--text-muted);">
                                    {f"Latency: {svc['latency']} · Uptime: {svc['uptime']}" if svc['latency'] != '—' else 'Not yet implemented · Phase 3/4'}
                                </div>
                            </div>
                        </div>
                        <div style="font-size:0.78rem;font-weight:600;color:{status_color};">{svc['status']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Real backend health check (preserved from Phase 1)
        st.markdown('<div class="section-title">🔌 Backend API Health Check</div>', unsafe_allow_html=True)
        api_url = os.environ.get("API_BASE_URL", "http://localhost:8000")
        st.markdown(f'<div class="text-muted">API URL: {api_url}</div>', unsafe_allow_html=True)

        if st.button("🔄 Check Backend API", key="health_check_btn", type="primary"):
            with st.spinner("Checking…"):
                result = check_backend_health()
            if result["online"]:
                data = result["data"]
                st.success(
                    f"✅ **Backend API Online** · "
                    f"Status: `{data.get('status')}` · "
                    f"Version: `{data.get('version')}` · "
                    f"Env: `{data.get('environment')}`"
                )
            else:
                st.warning(
                    f"⚠️ Backend not reachable: `{result['error']}` — "
                    "Start the backend with: `uvicorn backend.main:app --reload`"
                )

    with right:
        # Recent activity
        st.markdown('<div class="section-title">📜 Recent Activity</div>', unsafe_allow_html=True)
        audit = get_audit_log()[:8]
        type_colors = {
            "VALIDATE": "#1565c0", "ASSIGN": "#6B2737",
            "SUBMIT": "#2d6a4f", "AI": "#7b1fa2",
            "RESOLVE": "#2d6a4f",
        }
        for entry in audit:
            color = type_colors.get(entry["type"], "#9090a8")
            st.markdown(
                f"""
                <div class="complaint-card" style="padding:0.6rem 0.85rem;">
                    <div style="display:flex;gap:0.6rem;align-items:center;">
                        <div style="width:7px;height:7px;border-radius:50%;background:{color};flex-shrink:0;"></div>
                        <div style="flex:1;font-size:0.82rem;color:var(--text-primary);">{entry['action']}</div>
                        <div class="text-muted" style="white-space:nowrap;font-size:0.72rem;">{entry['time']}</div>
                    </div>
                    <div style="font-size:0.72rem;color:var(--text-muted);padding-left:1rem;">{entry['user']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="glass-card" style="padding:1rem;">
                <div class="section-title" style="margin-top:0;font-size:0.9rem;">📊 Quick Stats</div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem;font-size:0.83rem;">
                    <div>Active Users<br><strong>{len(active_users)}</strong></div>
                    <div>Total Users<br><strong>{len(all_users)}</strong></div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# User Management
# ---------------------------------------------------------------------------

def _render_users() -> None:
    st.markdown(
        '<div class="page-title">👥 User Management</div>'
        '<p class="page-subtitle">Manage all platform users across all roles.</p>',
        unsafe_allow_html=True,
    )

    users = get_all_users()
    role_filter = st.selectbox(
        "Filter by role",
        ["All", "Citizen", "Cleaner", "Municipal Staff", "Admin"],
        label_visibility="collapsed",
        key="user_role_filter",
    )
    filtered = [u for u in users if role_filter == "All" or u["role"] == role_filter]

    # Table-style display
    role_colors = {
        "Citizen": "#1565c0",
        "Cleaner": "#2d6a4f",
        "Municipal Staff": "#6B2737",
        "Admin": "#7b1fa2",
    }
    status_colors = {"Active": "#2d6a4f", "Inactive": "#c62828"}

    st.markdown("<br>", unsafe_allow_html=True)

    # Header
    st.markdown(
        """
        <div style="display:grid;grid-template-columns:2fr 2fr 1.5fr 1fr 1fr 1fr;gap:0.5rem;
                    padding:0.5rem 0.85rem;font-size:0.72rem;font-weight:600;
                    color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;
                    border-bottom:1px solid rgba(107,39,55,0.08);margin-bottom:0.25rem;">
            <span>Name</span><span>Email</span><span>Ward</span><span>Role</span><span>Status</span><span>Joined</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for u in filtered:
        rc = role_colors.get(u["role"], "#9090a8")
        sc = status_colors.get(u["status"], "#9090a8")
        st.markdown(
            f"""
            <div style="display:grid;grid-template-columns:2fr 2fr 1.5fr 1fr 1fr 1fr;gap:0.5rem;
                        padding:0.65rem 0.85rem;font-size:0.83rem;align-items:center;
                        border-bottom:1px solid rgba(107,39,55,0.05);">
                <span style="font-weight:500;">{u['name']}</span>
                <span style="color:var(--text-secondary);font-size:0.78rem;">{u['email']}</span>
                <span style="color:var(--text-muted);">{u['ward']}</span>
                <span style="color:{rc};font-weight:600;font-size:0.75rem;">{u['role']}</span>
                <span style="color:{sc};font-weight:600;font-size:0.75rem;">{u['status']}</span>
                <span style="color:var(--text-muted);font-size:0.75rem;">{u['joined']}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)
    st.button("➕ Add New User (Phase 3)", disabled=True, use_container_width=False)


# ---------------------------------------------------------------------------
# AI Monitoring
# ---------------------------------------------------------------------------

def _render_ai_monitoring() -> None:
    st.markdown(
        '<div class="page-title">🤖 AI Monitoring</div>'
        '<p class="page-subtitle">AI service health, model status, and performance metrics.</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="glass-card" style="background:rgba(107,39,55,0.04);border-color:rgba(107,39,55,0.15);">
            <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;">
                <span style="font-size:1.5rem;">🚧</span>
                <div>
                    <div style="font-weight:700;color:#6B2737;">Phase 3 Feature</div>
                    <div class="text-muted">AI Monitoring will be available when real AI services are implemented.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Show the stub services
    services = [
        ("🤖", "Waste Detector", "YOLO-based CV model for waste classification", "Phase 3", "waste_detector.detect(image)"),
        ("🧠", "Complaint Analyzer", "LangGraph agent for complaint analysis & prioritization", "Phase 3", "complaint_analyzer.analyze(complaint)"),
        ("🗺️", "Route Optimizer", "OR-Tools route optimization for cleaners", "Phase 4", "route_optimizer.optimize(tasks, cleaners)"),
        ("🔍", "Cleanup Verifier", "Before/after image comparison for verification", "Phase 4", "cleanup_verifier.verify(before, after)"),
        ("📚", "RAG Pipeline", "Self-corrective RAG for policy & awareness content", "Phase 3", "rag.query(question, context)"),
    ]

    for icon, name, desc, phase, interface in services:
        st.markdown(
            f"""
            <div class="glass-card" style="margin-bottom:0.5rem;">
                <div style="display:flex;align-items:flex-start;gap:0.75rem;">
                    <span style="font-size:1.4rem;">{icon}</span>
                    <div style="flex:1;">
                        <div style="font-weight:600;color:var(--text-primary);">{name}</div>
                        <div style="font-size:0.82rem;color:var(--text-secondary);margin:0.2rem 0;">{desc}</div>
                        <code style="font-size:0.75rem;background:rgba(107,39,55,0.08);padding:0.15em 0.5em;border-radius:4px;color:#6B2737;">{interface}</code>
                    </div>
                    <span class="badge badge-assigned" style="white-space:nowrap;">{phase}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Knowledge Base
# ---------------------------------------------------------------------------

def _render_knowledge_base() -> None:
    st.markdown(
        '<div class="page-title">📚 Knowledge Base</div>'
        '<p class="page-subtitle">Manage awareness content and policy documents for RAG.</p>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="glass-card" style="background:rgba(107,39,55,0.04);">
            <div style="font-weight:700;color:#6B2737;margin-bottom:0.5rem;">🚧 Phase 3 Feature</div>
            <div style="font-size:0.85rem;color:var(--text-secondary);">
                The Knowledge Base will contain:
                <ul style="margin-top:0.5rem;line-height:2;">
                    <li>Municipal waste management policies</li>
                    <li>Awareness content (Malayalam + English)</li>
                    <li>Kerala Pollution Control Board guidelines</li>
                    <li>Ward-specific rules and contacts</li>
                    <li>Escalation procedures</li>
                </ul>
                This will power the Self-Corrective RAG pipeline for intelligent query answering.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.button("📤 Upload Document (Phase 3)", disabled=True)
    st.button("🔍 Test RAG Query (Phase 3)", disabled=True)


# ---------------------------------------------------------------------------
# Audit Logs
# ---------------------------------------------------------------------------

def _render_audit_logs() -> None:
    st.markdown(
        '<div class="page-title">📜 Audit Logs</div>'
        '<p class="page-subtitle">All user and system actions recorded for accountability.</p>',
        unsafe_allow_html=True,
    )

    log = get_audit_log()
    type_colors = {
        "VALIDATE": "#1565c0", "ASSIGN": "#6B2737",
        "SUBMIT": "#2d6a4f", "AI": "#7b1fa2",
        "RESOLVE": "#2d6a4f",
    }
    type_labels = {
        "VALIDATE": "Validate", "ASSIGN": "Assign",
        "SUBMIT": "Submit", "AI": "AI Auto",
        "RESOLVE": "Resolve",
    }

    # Header
    st.markdown(
        """
        <div style="display:grid;grid-template-columns:1.5fr 2fr 4fr 1fr;gap:0.5rem;
                    padding:0.5rem 1rem;font-size:0.72rem;font-weight:600;
                    color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em;
                    border-bottom:1px solid rgba(107,39,55,0.08);margin-bottom:0.25rem;">
            <span>Time</span><span>User</span><span>Action</span><span>Type</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for entry in log:
        color = type_colors.get(entry["type"], "#9090a8")
        label = type_labels.get(entry["type"], entry["type"])
        st.markdown(
            f"""
            <div style="display:grid;grid-template-columns:1.5fr 2fr 4fr 1fr;gap:0.5rem;
                        padding:0.65rem 1rem;font-size:0.82rem;align-items:center;
                        border-bottom:1px solid rgba(107,39,55,0.05);">
                <span class="text-muted" style="font-size:0.75rem;">{entry['time']}</span>
                <span style="font-size:0.78rem;color:var(--text-secondary);">{entry['user']}</span>
                <span>{entry['action']}</span>
                <span style="color:{color};font-weight:600;font-size:0.72rem;">{label}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="text-muted" style="margin-top:0.75rem;">Phase 3: Full audit trail with user authentication tokens and DB-backed log storage.</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

def _render_settings() -> None:
    st.markdown(
        '<div class="page-title">⚙️ Settings</div>'
        '<p class="page-subtitle">System configuration and environment settings.</p>',
        unsafe_allow_html=True,
    )

    api_url = os.environ.get("API_BASE_URL", "http://localhost:8000")

    st.markdown(
        f"""
        <div class="glass-card">
            <div class="section-title" style="margin-top:0;">🔗 API Configuration</div>
            <div style="display:grid;grid-template-columns:auto 1fr;gap:0.5rem 1.5rem;font-size:0.85rem;">
                <span style="color:var(--text-muted);">Backend URL</span><span class="mono">{api_url}</span>
                <span style="color:var(--text-muted);">Frontend Port</span><span class="mono">8501</span>
                <span style="color:var(--text-muted);">Environment</span><span>Development (Phase 2)</span>
                <span style="color:var(--text-muted);">Version</span><span>v0.2.0</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="glass-card" style="background:rgba(107,39,55,0.04);margin-top:0.5rem;">
            <div class="section-title" style="margin-top:0;">🚧 Phase 3+ Settings</div>
            <div style="font-size:0.85rem;color:var(--text-secondary);">
                The following settings will be configurable in Phase 3:
            </div>
            <ul style="font-size:0.83rem;color:var(--text-muted);line-height:2;margin-top:0.5rem;">
                <li>AI model selection (YOLO variant, LLM provider)</li>
                <li>Priority thresholds and SLA timers</li>
                <li>Ward/zone configuration</li>
                <li>Notification preferences (Telegram, etc.)</li>
                <li>Database connection settings</li>
                <li>User role permissions</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )
