"""
SwachhLoop AI — Municipal Staff Dashboard & Sub-pages
======================================================
Phase 2: Full prototype — most information-rich dashboard.
Phase 3: Connect to real API via frontend/services/api_client.py

Sub-pages:
    dashboard    — KPIs, AI queue, recent activity
    complaints   — Full complaint queue
    waste_map    — Waste hotspot map
    tasks        — Cleaner task overview
    escalations  — Escalated complaints
    analytics    — Stats overview
    notifications — Feed
    profile      — Staff profile
"""

import streamlit as st

from frontend.components import (
    render_topbar, stat_card, complaint_card,
    render_timeline, render_map, render_notifications,
    status_badge_html, priority_badge_html,
)
from frontend.components.cards import ai_assessment_card
from frontend.services.api_client import (
    get_complaints, get_complaint_by_id, get_tasks,
    get_notifications, get_map_markers, get_municipal_stats,
    get_audit_log, assign_complaint, update_complaint_status, get_cleaners,
)


def render() -> None:
    user = st.session_state.get("user", {})
    current_page = st.session_state.get("current_page", "dashboard")

    render_topbar(user, "municipal_staff", current_page.replace("_", " ").title())

    if "selected_complaint" in st.session_state:
        _render_complaint_detail(st.session_state["selected_complaint"])
    elif current_page == "dashboard":
        _render_dashboard(user)
    elif current_page == "complaints":
        _render_complaints()
    elif current_page == "waste_map":
        _render_waste_map()
    elif current_page == "tasks":
        _render_tasks()
    elif current_page == "escalations":
        _render_escalations()
    elif current_page == "analytics":
        _render_analytics()
    elif current_page == "notifications":
        render_notifications(get_notifications("municipal_staff"), "municipal_staff")
    elif current_page == "profile":
        _render_profile(user)
    else:
        _render_dashboard(user)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def _render_dashboard(user: dict) -> None:
    stats = get_municipal_stats()
    name = user.get("name", "").split()[0]

    st.markdown(
        f"""
        <div class="glass-card" style="padding:1.25rem 1.5rem;margin-bottom:1.25rem;">
            <div class="page-title">Operations Dashboard</div>
            <p class="page-subtitle">Welcome back, {name}. Here's the real-time waste management overview.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # KPI row 1
    c1, c2, c3, c4 = st.columns(4)
    with c1: stat_card("Total Complaints", stats["total_complaints"], "📋", "brand")
    with c2: stat_card("Pending Review", stats["pending"], "⏳", "warning")
    with c3: stat_card("Being Cleaned", stats["cleaning"], "🧹", "default")
    with c4: stat_card("Resolved", stats["resolved"], "✅", "success")

    st.markdown("<br>", unsafe_allow_html=True)

    # KPI row 2
    c5, c6, c7, c8 = st.columns(4)
    with c5: stat_card("Validated", stats["validated"], "✅", "default")
    with c6: stat_card("Assigned", stats["assigned"], "👷", "default")
    with c7: stat_card("Verification", stats["verification"], "🔍", "default")
    with c8: stat_card("Escalated", stats["escalated"], "⚠️", "critical")

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1, 1])

    with left:
        # AI Priority Queue
        st.markdown('<div class="section-title">🤖 AI Priority Queue</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="text-muted" style="margin-bottom:0.5rem;">Demo values · Phase 3 will use real AI scoring</div>',
            unsafe_allow_html=True,
        )

        priority_queue = [
            {
                "id": "CMP-2024-0871",
                "priority": "CRITICAL",
                "title": "Biomedical Waste — Ward 5",
                "reason": "High-risk waste type detected near residential area.",
                "confidence": 96,
            },
            {
                "id": "CMP-2024-0891",
                "priority": "CRITICAL",
                "title": "Illegal Dumping — Gandhi Park",
                "reason": "Large accumulation blocking public footpath.",
                "confidence": 94,
            },
            {
                "id": "CMP-2024-0868",
                "priority": "HIGH",
                "title": "Open Burning — Canal Road, Ward 9",
                "reason": "Active burning detected, air quality risk.",
                "confidence": 85,
            },
            {
                "id": "CMP-2024-0879",
                "priority": "MEDIUM",
                "title": "Plastic Waste — School Zone",
                "reason": "Plastic accumulation near school entrance.",
                "confidence": 91,
            },
        ]

        for item in priority_queue:
            priority_color = {"CRITICAL": "#c62828", "HIGH": "#e65100", "MEDIUM": "#f57f17", "LOW": "#2d6a4f"}.get(item["priority"], "#9090a8")
            st.markdown(
                f"""
                <div class="complaint-card" style="border-left:4px solid {priority_color};margin-bottom:0.5rem;">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem;">
                        <div style="flex:1;">
                            <div class="complaint-card-id">{item['id']} · AI: {item['confidence']}% confidence</div>
                            <div class="complaint-card-title">{item['title']}</div>
                            <div class="complaint-card-meta">{item['reason']}</div>
                        </div>
                        <div>{priority_badge_html(item['priority'])}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            col_v, col_a = st.columns([1, 1])
            with col_v:
                if st.button("View", key=f"queue_view_{item['id']}", use_container_width=True):
                    st.session_state["selected_complaint"] = item["id"]
                    st.rerun()
            with col_a:
                st.button("Assign Cleaner", key=f"queue_assign_{item['id']}", use_container_width=True, type="primary")

    with right:
        # Waste map
        st.markdown('<div class="section-title">🗺️ Waste Hotspot Map</div>', unsafe_allow_html=True)
        render_map(get_map_markers(), height=280, show_legend=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Cleaner availability
        st.markdown(
            f"""
            <div class="glass-card" style="padding:1rem;">
                <div class="section-title" style="margin-top:0;font-size:0.9rem;">👷 Cleaner Availability</div>
                <div style="display:flex;gap:2rem;">
                    <div style="text-align:center;">
                        <div style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:700;color:#2d6a4f;">{stats['cleaners_available']}</div>
                        <div class="text-muted">Available</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:700;color:#6B2737;">{stats['cleaners_on_task']}</div>
                        <div class="text-muted">On Task</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-family:'Outfit',sans-serif;font-size:1.5rem;font-weight:700;color:#1565c0;">{stats['avg_resolution_hours']}h</div>
                        <div class="text-muted">Avg Resolution</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Recent Activity
    st.markdown('<div class="section-title">📜 Recent Activity</div>', unsafe_allow_html=True)
    audit_log = get_audit_log()[:5]
    type_colors = {
        "VALIDATE": "#1565c0", "ASSIGN": "#6B2737",
        "SUBMIT": "#2d6a4f", "AI": "#7b1fa2",
        "RESOLVE": "#2d6a4f",
    }
    for entry in audit_log:
        color = type_colors.get(entry["type"], "#9090a8")
        st.markdown(
            f"""
            <div class="complaint-card" style="padding:0.65rem 1rem;">
                <div style="display:flex;gap:0.75rem;align-items:center;">
                    <div style="width:8px;height:8px;border-radius:50%;background:{color};flex-shrink:0;"></div>
                    <div style="flex:1;font-size:0.83rem;color:var(--text-primary);">{entry['action']}</div>
                    <div class="text-muted" style="white-space:nowrap;">{entry['time']}</div>
                </div>
                <div style="font-size:0.73rem;color:var(--text-muted);padding-left:1.1rem;">{entry['user']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Complaint Queue
# ---------------------------------------------------------------------------

def _render_complaints() -> None:
    st.markdown(
        '<div class="page-title">📋 Complaint Queue</div>'
        '<p class="page-subtitle">All incoming waste complaints. Validate, assign, and track.</p>',
        unsafe_allow_html=True,
    )

    complaints = get_complaints()
    tabs = st.tabs(["All", "Pending Review", "In Progress", "Resolved"])

    with tabs[0]:
        for c in complaints:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                clicked = complaint_card(c, show_action=True, action_label="View")
                if clicked:
                    st.session_state["selected_complaint"] = c["id"]
                    st.rerun()

    with tabs[1]:
        pending = [c for c in complaints if c["status"] in ("SUBMITTED",)]
        for c in pending:
            clicked = complaint_card(c, show_action=True, action_label="Validate")
            if clicked:
                st.session_state["selected_complaint"] = c["id"]
                st.rerun()

    with tabs[2]:
        in_prog = [c for c in complaints if c["status"] in ("VALIDATED", "ASSIGNED", "CLEANING", "VERIFICATION")]
        for c in in_prog:
            clicked = complaint_card(c, show_action=True, action_label="View")
            if clicked:
                st.session_state["selected_complaint"] = c["id"]
                st.rerun()

    with tabs[3]:
        resolved = [c for c in complaints if c["status"] == "RESOLVED"]
        for c in resolved:
            complaint_card(c, show_action=False)


# ---------------------------------------------------------------------------
# Complaint Detail (Municipal Staff)
# ---------------------------------------------------------------------------

def _render_complaint_detail(complaint_id: str) -> None:
    complaint = get_complaint_by_id(complaint_id)
    if not complaint:
        st.error(f"Complaint {complaint_id} not found.")
        if st.button("← Back"):
            del st.session_state["selected_complaint"]
            st.rerun()
        return

    if st.button("← Back to Complaints", key="staff_back_btn"):
        del st.session_state["selected_complaint"]
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Header
    st.markdown(
        f"""
        <div class="glass-card">
            <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:0.75rem;align-items:flex-start;">
                <div>
                    <div class="complaint-card-id">{complaint['id']}</div>
                    <div class="page-title" style="font-size:1.4rem;">{complaint['title']}</div>
                    <div class="page-subtitle">📍 {complaint['location']} · 🕐 {complaint['reported_at']}</div>
                    <div class="page-subtitle">👤 Reported by: {complaint['citizen_name']}</div>
                </div>
                <div style="display:flex;flex-direction:column;gap:0.3rem;align-items:flex-end;">
                    {priority_badge_html(complaint['priority'])}
                    {status_badge_html(complaint['status'])}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1])

    with left:
        # AI Assessment
        ai_assessment_card(
            waste_type=complaint.get("waste_type", "Unknown"),
            confidence=complaint.get("ai_confidence", 0),
            priority=complaint.get("priority", "MEDIUM"),
            reason=complaint.get("ai_reason", "—"),
        )

        # Description
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title" style="margin-top:0;">📝 Complaint Description</div>
                <div style="font-size:0.88rem;color:var(--text-secondary);line-height:1.7;">{complaint.get('description','—')}</div>
                <hr class="styled">
                <div style="display:grid;grid-template-columns:auto 1fr;gap:0.4rem 1rem;font-size:0.83rem;">
                    <span style="color:var(--text-muted);">Assigned To</span>
                    <span style="font-weight:500;">{complaint.get('assigned_cleaner') or 'Not assigned'}</span>
                    <span style="color:var(--text-muted);">Assigned At</span>
                    <span>{complaint.get('assigned_at','—')}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Action buttons
        st.markdown('<div class="section-title">Actions</div>', unsafe_allow_html=True)
        col_a, col_b = st.columns(2)
        with col_a:
            cleaners_list = get_cleaners()
            cleaner_names = [f"{c['name']} (ID #{c['id']})" for c in cleaners_list] if cleaners_list else ["Rajan Pillai (ID #2)"]
            selected_cleaner_label = st.selectbox("Assign Cleaner", cleaner_names, key=f"assign_{complaint_id}")
            if st.button("👷 Assign", type="primary", key=f"assign_btn_{complaint_id}", use_container_width=True):
                idx = cleaner_names.index(selected_cleaner_label)
                cleaner_id = cleaners_list[idx]["id"] if cleaners_list else 2
                res = assign_complaint(complaint_id, cleaner_id)
                st.success(f"Assigned {selected_cleaner_label} to complaint #{complaint_id}.")
                st.rerun()
        with col_b:
            new_status_val = st.selectbox("Update Status", ["VALIDATED", "ASSIGNED", "CLEANING", "VERIFICATION", "RESOLVED", "ESCALATED"], key=f"status_sel_{complaint_id}")
            if st.button("🔄 Update Status", key=f"status_btn_{complaint_id}", use_container_width=True):
                res = update_complaint_status(complaint_id, new_status_val)
                st.success(f"Status updated to {new_status_val}.")
                st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        col_c, col_d = st.columns(2)
        with col_c:
            st.button("⚠️ Escalate", key=f"escalate_{complaint_id}", use_container_width=True)
        with col_d:
            st.button("🗺️ View on Map", key=f"map_{complaint_id}", use_container_width=True)

    with right:
        st.markdown('<div class="section-title">🕐 Status Timeline</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        render_timeline(complaint.get("timeline", []))
        st.markdown("</div>", unsafe_allow_html=True)

        if complaint.get("lat"):
            render_map(
                [{"lat": complaint["lat"], "lon": complaint["lon"], "type": complaint["priority"], "label": complaint["location"]}],
                height=200,
                title="Location",
                show_legend=False,
            )


# ---------------------------------------------------------------------------
# Waste Map
# ---------------------------------------------------------------------------

def _render_waste_map() -> None:
    st.markdown(
        '<div class="page-title">🗺️ Waste Hotspot Map</div>'
        '<p class="page-subtitle">All active and resolved waste complaints by location.</p>',
        unsafe_allow_html=True,
    )

    filter_col, _ = st.columns([1, 2])
    with filter_col:
        filter_type = st.selectbox(
            "Filter markers",
            ["All", "CRITICAL", "HIGH", "MEDIUM", "LOW", "RESOLVED"],
            label_visibility="collapsed",
        )

    markers = get_map_markers(None if filter_type == "All" else filter_type)
    render_map(markers, height=420, show_legend=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="text-muted">Phase 4: Interactive Leaflet map with real-time complaint pins, clustering, and route overlays.</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Tasks Overview
# ---------------------------------------------------------------------------

def _render_tasks() -> None:
    st.markdown(
        '<div class="page-title">✅ Task Overview</div>'
        '<p class="page-subtitle">All cleanup tasks and their cleaner assignments.</p>',
        unsafe_allow_html=True,
    )

    from frontend.components.cards import task_card
    tasks = get_tasks()
    for t in tasks:
        task_card(t)


# ---------------------------------------------------------------------------
# Escalations
# ---------------------------------------------------------------------------

def _render_escalations() -> None:
    st.markdown(
        '<div class="page-title">⚠️ Escalations</div>'
        '<p class="page-subtitle">Complaints requiring urgent attention or management review.</p>',
        unsafe_allow_html=True,
    )

    escalated = [c for c in get_complaints() if c.get("priority") == "CRITICAL" and c["status"] not in ("RESOLVED",)]

    if not escalated:
        st.markdown(
            '<div class="glass-card" style="text-align:center;padding:3rem;color:var(--text-muted);">✅ No active escalations.</div>',
            unsafe_allow_html=True,
        )
        return

    for c in escalated:
        clicked = complaint_card(c, show_action=True, action_label="Manage")
        if clicked:
            st.session_state["selected_complaint"] = c["id"]
            st.rerun()


# ---------------------------------------------------------------------------
# Analytics
# ---------------------------------------------------------------------------

def _render_analytics() -> None:
    stats = get_municipal_stats()
    st.markdown(
        '<div class="page-title">📊 Analytics</div>'
        '<p class="page-subtitle">Waste management performance metrics.</p>',
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1: stat_card("Total Complaints", stats["total_complaints"], "📋", "brand")
    with c2: stat_card("Avg Resolution", f"{stats['avg_resolution_hours']}h", "⏱️", "default")
    with c3: stat_card("Resolution Rate", f"{int(stats['resolved']/(stats['total_complaints']+stats['resolved'])*100)}%", "📈", "success")

    st.markdown("<br>", unsafe_allow_html=True)

    # Status breakdown
    st.markdown(
        f"""
        <div class="glass-card">
            <div class="section-title" style="margin-top:0;">Complaint Status Breakdown</div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;text-align:center;">
                <div>
                    <div style="font-size:1.5rem;font-weight:700;color:#9090a8;">{stats['pending']}</div>
                    <div class="text-muted">Pending</div>
                </div>
                <div>
                    <div style="font-size:1.5rem;font-weight:700;color:#e65100;">{stats['assigned']}</div>
                    <div class="text-muted">Assigned</div>
                </div>
                <div>
                    <div style="font-size:1.5rem;font-weight:700;color:#6B2737;">{stats['cleaning']}</div>
                    <div class="text-muted">Cleaning</div>
                </div>
                <div>
                    <div style="font-size:1.5rem;font-weight:700;color:#2d6a4f;">{stats['resolved']}</div>
                    <div class="text-muted">Resolved</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="text-muted" style="margin-top:1rem;">Phase 3: Real analytics charts with Altair/Plotly will be added here.</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def _render_profile(user: dict) -> None:
    st.markdown(
        '<div class="page-title">👤 My Profile</div>',
        unsafe_allow_html=True,
    )
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align:center;padding:2rem;">
                <div class="avatar" style="width:60px;height:60px;font-size:1.3rem;margin:0 auto 1rem;">{user.get('avatar_initials','?')}</div>
                <div style="font-family:'Outfit',sans-serif;font-size:1.1rem;font-weight:700;">{user.get('name','—')}</div>
                <div style="font-size:0.82rem;color:var(--text-secondary);">{user.get('email','—')}</div>
                <div class="sidebar-role-chip" style="margin-top:0.5rem;">Municipal Staff</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title" style="margin-top:0;">Details</div>
                <div style="display:grid;grid-template-columns:auto 1fr;gap:0.5rem 1.5rem;font-size:0.85rem;">
                    <span style="color:var(--text-muted);">Department</span><span>{user.get('department','—')}</span>
                    <span style="color:var(--text-muted);">Phone</span><span>{user.get('phone','—')}</span>
                    <span style="color:var(--text-muted);">Employee ID</span><span>{user.get('employee_id','—')}</span>
                    <span style="color:var(--text-muted);">Member Since</span><span>{user.get('joined','—')}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
