"""
SwachhLoop AI — Cleaner Dashboard & Sub-pages
===============================================
Phase 2: Full prototype with mock data.
Phase 3: Connect to real API via frontend/services/api_client.py

Sub-pages:
    dashboard    — Overview, today's tasks, stats
    my_tasks     — Task list with filtering
    map          — Task map view
    task_history — Completed tasks
    notifications — Notification feed
    profile      — Cleaner profile
"""

import streamlit as st
import datetime

from frontend.components import (
    render_topbar, stat_card, task_card,
    render_timeline, render_map, render_notifications,
    status_badge_html, priority_badge_html,
)
from frontend.services.api_client import (
    get_tasks, get_task_by_id, update_task_status,
    get_notifications, get_map_markers,
)


def render() -> None:
    """Entry point — routes to the appropriate cleaner sub-page."""
    user = st.session_state.get("user", {})
    current_page = st.session_state.get("current_page", "dashboard")

    render_topbar(user, "cleaner", current_page.replace("_", " ").title())

    if "selected_task" in st.session_state:
        _render_task_detail(st.session_state["selected_task"])
    elif current_page == "dashboard":
        _render_dashboard(user)
    elif current_page == "my_tasks":
        _render_my_tasks()
    elif current_page == "map":
        _render_map_view()
    elif current_page == "task_history":
        _render_task_history()
    elif current_page == "notifications":
        render_notifications(get_notifications("cleaner"), "cleaner")
    elif current_page == "profile":
        _render_profile(user)
    else:
        _render_dashboard(user)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def _render_dashboard(user: dict) -> None:
    name = user.get("name", "").split()[0]
    tasks = get_tasks(cleaner_id=user.get("id", "u002"))

    today_tasks = [t for t in tasks if t["status"] in ("PENDING", "IN_PROGRESS")]
    completed = [t for t in tasks if t["status"] == "COMPLETED"]
    critical = [t for t in today_tasks if t["priority"] == "CRITICAL"]
    high = [t for t in today_tasks if t["priority"] == "HIGH"]

    # Greeting
    c_greet, c_action = st.columns([3, 1])
    with c_greet:
        st.markdown(
            f"""
            <div class="glass-card" style="padding:1.25rem 1.5rem;margin-bottom:1.25rem;">
                <div class="page-title">Good morning, {name} 👷</div>
                <div class="page-subtitle">You have <strong>{len(today_tasks)}</strong> tasks assigned today.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_action:
        st.markdown('<div style="height:0.8rem;"></div>', unsafe_allow_html=True)
        if st.button("📋 View My Tasks", type="primary", key="goto_tasks_btn", use_container_width=True):
            st.session_state["current_page"] = "my_tasks"
            st.rerun()

    # KPIs
    c1, c2, c3, c4 = st.columns(4)
    with c1: stat_card("Tasks Today", len(today_tasks), "📋", "brand")
    with c2: stat_card("Critical", len(critical), "🔴", "critical")
    with c3: stat_card("High Priority", len(high), "🟠", "warning")
    with c4: stat_card("Completed", len(completed), "✅", "success")

    st.markdown("<br>", unsafe_allow_html=True)

    left, right = st.columns([1.2, 1])

    with left:
        st.markdown('<div class="section-title">📋 Today\'s Priority Tasks</div>', unsafe_allow_html=True)
        if not today_tasks:
            st.markdown(
                '<div class="glass-card" style="text-align:center;padding:2rem;color:var(--text-muted);">🎉 No pending tasks! Great job.</div>',
                unsafe_allow_html=True,
            )
        else:
            # Show top 3 by priority order
            priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
            sorted_tasks = sorted(today_tasks, key=lambda t: priority_order.get(t["priority"], 9))
            for t in sorted_tasks[:3]:
                clicked = task_card(t)
                if clicked:
                    st.session_state["selected_task"] = t["id"]
                    st.rerun()

    with right:
        st.markdown('<div class="section-title">🗺️ Task Map</div>', unsafe_allow_html=True)
        # Build cleaner-specific markers
        task_markers = []
        for t in today_tasks:
            if t.get("lat"):
                task_markers.append({
                    "lat": t["lat"], "lon": t["lon"],
                    "type": t["priority"],
                    "label": t["title"],
                })
        render_map(task_markers or get_map_markers(), height=240, show_legend=True)

        # Cleaner stats
        st.markdown(
            f"""
            <div class="glass-card" style="margin-top:0.75rem;padding:1rem;">
                <div class="section-title" style="margin-top:0;font-size:0.9rem;">📊 My Stats</div>
                <div style="display:flex;gap:1.5rem;flex-wrap:wrap;">
                    <div style="text-align:center;">
                        <div style="font-family:'Outfit',sans-serif;font-size:1.4rem;font-weight:700;color:#6B2737;">{user.get('tasks_completed',0)}</div>
                        <div class="text-muted">Total Completed</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-family:'Outfit',sans-serif;font-size:1.4rem;font-weight:700;color:#2d6a4f;">98%</div>
                        <div class="text-muted">Verification Rate</div>
                    </div>
                    <div style="text-align:center;">
                        <div style="font-family:'Outfit',sans-serif;font-size:1.4rem;font-weight:700;color:#1565c0;">22 min</div>
                        <div class="text-muted">Avg Task Time</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# My Tasks
# ---------------------------------------------------------------------------

def _render_my_tasks() -> None:
    st.markdown(
        '<div class="page-title">✅ My Tasks</div>'
        '<p class="page-subtitle">All tasks assigned to you.</p>',
        unsafe_allow_html=True,
    )

    tasks = get_tasks()

    status_filter = st.selectbox(
        "Filter",
        options=["All", "PENDING", "IN_PROGRESS", "COMPLETED"],
        label_visibility="collapsed",
        key="tasks_filter",
    )
    filtered = [t for t in tasks if status_filter == "All" or t["status"] == status_filter]

    st.markdown("<br>", unsafe_allow_html=True)

    if not filtered:
        st.markdown(
            '<div class="glass-card" style="text-align:center;padding:3rem;color:var(--text-muted);">No tasks found.</div>',
            unsafe_allow_html=True,
        )
        return

    priority_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3}
    sorted_tasks = sorted(filtered, key=lambda t: (priority_order.get(t["priority"], 9),
                                                    0 if t["status"] == "IN_PROGRESS" else 1))
    for t in sorted_tasks:
        clicked = task_card(t)
        if clicked:
            st.session_state["selected_task"] = t["id"]
            st.rerun()


# ---------------------------------------------------------------------------
# Task Detail
# ---------------------------------------------------------------------------

def _render_task_detail(task_id: str) -> None:
    task = get_task_by_id(task_id)
    if not task:
        st.error(f"Task {task_id} not found.")
        if st.button("← Back"):
            del st.session_state["selected_task"]
            st.rerun()
        return

    if st.button("← Back to Tasks", key="back_from_task"):
        del st.session_state["selected_task"]
        if "task_state" in st.session_state:
            del st.session_state["task_state"]
        if "task_upload" in st.session_state:
            del st.session_state["task_upload"]
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    task_state = st.session_state.get("task_state", task.get("status", "PENDING"))

    # Header
    priority_color = {"CRITICAL": "#c62828", "HIGH": "#e65100", "MEDIUM": "#f57f17", "LOW": "#2d6a4f"}.get(task["priority"], "#9090a8")
    st.markdown(
        f"""
        <div class="glass-card" style="border-left:5px solid {priority_color};">
            <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:0.75rem;align-items:flex-start;">
                <div>
                    <div class="complaint-card-id">{task['id']} · {task['complaint_id']}</div>
                    <div class="page-title" style="font-size:1.4rem;">{task['title']}</div>
                    <div class="page-subtitle">📍 {task['location']}</div>
                </div>
                <div style="display:flex;flex-direction:column;gap:0.3rem;align-items:flex-end;">
                    {priority_badge_html(task['priority'])}
                    {status_badge_html(task_state)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1])

    with left:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title" style="margin-top:0;">📋 Task Details</div>
                <div style="display:grid;grid-template-columns:auto 1fr;gap:0.5rem 1rem;font-size:0.85rem;">
                    <span style="color:var(--text-muted);">Waste Type</span><span style="font-weight:500;">{task['waste_type']}</span>
                    <span style="color:var(--text-muted);">Distance</span><span style="font-weight:500;">{task['distance']}</span>
                    <span style="color:var(--text-muted);">Est. Time</span><span style="font-weight:500;">{task['estimated_time']}</span>
                    <span style="color:var(--text-muted);">Assigned</span><span style="font-weight:500;">{task['assigned_at']}</span>
                </div>
                <hr class="styled">
                <div style="font-size:0.85rem;color:var(--text-secondary);line-height:1.7;">{task['description']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Actions based on state
        if task_state == "PENDING":
            col_nav, col_start = st.columns(2)
            with col_nav:
                if st.button("🗺️ Navigate", use_container_width=True):
                    st.info("Navigation opens your maps app. (Phase 3: real GPS routing)", icon="🗺️")
            with col_start:
                if st.button("▶️ Start Cleaning", type="primary", use_container_width=True):
                    st.session_state["task_state"] = "IN_PROGRESS"
                    st.rerun()

        elif task_state == "IN_PROGRESS":
            st.markdown(
                """
                <div class="glass-card" style="background:rgba(107,39,55,0.05);border-color:rgba(107,39,55,0.2);text-align:center;padding:1rem;">
                    <div style="font-size:1.2rem;margin-bottom:0.3rem;">🧹</div>
                    <div style="font-weight:600;color:#6B2737;">Cleaning In Progress</div>
                    <div class="text-muted">Upload an after photo to submit for verification.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            uploaded = st.file_uploader(
                "📷 Upload After Photo",
                type=["jpg", "jpeg", "png"],
                key="after_photo",
                help="This photo will be compared with the before image for AI verification.",
            )
            if uploaded:
                st.image(uploaded, caption="After cleanup photo — preview", use_container_width=True)

            if st.button("📤 Submit for Verification", type="primary", use_container_width=True):
                if uploaded:
                    st.session_state["task_state"] = "COMPLETED"
                    update_task_status(task_id, "COMPLETED")
                    st.rerun()
                else:
                    st.warning("Please upload an after photo before submitting.")

        elif task_state == "COMPLETED":
            st.markdown(
                """
                <div class="success-banner" style="padding:1.5rem;">
                    <div class="success-icon">🎉</div>
                    <div class="success-title">Task Submitted for Verification!</div>
                    <div style="color:#5a5a7a;font-size:0.85rem;margin-top:0.3rem;">
                        Municipal staff will verify the cleanup. You'll be notified once it's confirmed.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(
                '<div class="text-muted" style="margin-top:0.5rem;">Phase 3: AI will automatically compare before/after images for instant verification.</div>',
                unsafe_allow_html=True,
            )

    with right:
        if task.get("lat"):
            render_map(
                [{"lat": task["lat"], "lon": task["lon"], "type": task["priority"], "label": task["location"]}],
                height=220,
                title="Location",
                show_legend=False,
            )


# ---------------------------------------------------------------------------
# Map View
# ---------------------------------------------------------------------------

def _render_map_view() -> None:
    st.markdown(
        '<div class="page-title">🗺️ Task Map</div>'
        '<p class="page-subtitle">All your assigned tasks on the map.</p>',
        unsafe_allow_html=True,
    )

    tasks = get_tasks()
    markers = []
    for t in tasks:
        if t.get("lat"):
            markers.append({
                "lat": t["lat"], "lon": t["lon"],
                "type": t["priority"],
                "label": f"{t['id']}: {t['title']}",
            })
    render_map(markers, height=400, show_legend=True)
    st.markdown(
        '<div class="text-muted">Phase 4: Interactive map with optimized route display using OR-Tools.</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Task History
# ---------------------------------------------------------------------------

def _render_task_history() -> None:
    st.markdown(
        '<div class="page-title">📂 Task History</div>'
        '<p class="page-subtitle">Your completed cleanup tasks.</p>',
        unsafe_allow_html=True,
    )

    tasks = get_tasks()
    completed = [t for t in tasks if t["status"] == "COMPLETED"]

    if not completed:
        st.markdown(
            '<div class="glass-card" style="text-align:center;padding:3rem;color:var(--text-muted);">No completed tasks yet.</div>',
            unsafe_allow_html=True,
        )
        return

    for t in completed:
        st.markdown(
            f"""
            <div class="complaint-card" style="border-left:4px solid #2d6a4f;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;">
                    <div>
                        <div class="complaint-card-id">{t['id']}</div>
                        <div class="complaint-card-title">{t['title']}</div>
                        <div class="complaint-card-meta">📍 {t['location']} · {t['waste_type']}</div>
                    </div>
                    <div>{status_badge_html(t['status'])}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def _render_profile(user: dict) -> None:
    st.markdown(
        '<div class="page-title">👤 My Profile</div>'
        '<p class="page-subtitle">Your account and performance details.</p>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align:center;padding:2rem;">
                <div class="avatar" style="width:60px;height:60px;font-size:1.3rem;margin:0 auto 1rem;">{user.get('avatar_initials','?')}</div>
                <div style="font-family:'Outfit',sans-serif;font-size:1.1rem;font-weight:700;">{user.get('name','—')}</div>
                <div style="font-size:0.82rem;color:var(--text-secondary);margin:0.2rem 0;">{user.get('email','—')}</div>
                <div class="sidebar-role-chip" style="margin-top:0.5rem;">Cleaner</div>
                <div class="text-muted">Employee ID: {user.get('employee_id','—')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title" style="margin-top:0;">Work Summary</div>
                <div style="display:grid;grid-template-columns:auto 1fr;gap:0.5rem 1.5rem;font-size:0.85rem;">
                    <span style="color:var(--text-muted);">Zone</span><span>{user.get('ward','—')}</span>
                    <span style="color:var(--text-muted);">Phone</span><span>{user.get('phone','—')}</span>
                    <span style="color:var(--text-muted);">Member since</span><span>{user.get('joined','—')}</span>
                    <span style="color:var(--text-muted);">Tasks Completed</span>
                    <span style="font-weight:700;color:#2d6a4f;">{user.get('tasks_completed',0)}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
