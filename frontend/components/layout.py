"""
SwachhLoop AI — Layout Components
====================================
Sidebar navigation and top bar rendering.
"""

import streamlit as st


# ---------------------------------------------------------------------------
# Navigation configs per role
# ---------------------------------------------------------------------------

ROLE_LABELS = {
    "citizen":        "Citizen",
    "cleaner":        "Cleaner",
    "municipal_staff": "Municipal Staff",
    "admin":          "Admin",
}

ROLE_NAV = {
    "citizen": [
        ("dashboard",       "🏠", "Dashboard"),
        ("report_waste",    "📸", "Report Waste"),
        ("my_complaints",   "📋", "My Complaints"),
        ("nearby_issues",   "📍", "Nearby Issues"),
        ("awareness",       "💡", "Awareness"),
        ("notifications",   "🔔", "Notifications"),
        ("profile",         "👤", "Profile"),
    ],
    "cleaner": [
        ("dashboard",       "🏠", "Dashboard"),
        ("my_tasks",        "✅", "My Tasks"),
        ("map",             "🗺️", "Map"),
        ("task_history",    "📂", "Task History"),
        ("notifications",   "🔔", "Notifications"),
        ("profile",         "👤", "Profile"),
    ],
    "municipal_staff": [
        ("dashboard",       "🏠", "Dashboard"),
        ("complaints",      "📋", "Complaints"),
        ("waste_map",       "🗺️", "Waste Map"),
        ("tasks",           "✅", "Tasks"),
        ("escalations",     "⚠️", "Escalations"),
        ("analytics",       "📊", "Analytics"),
        ("notifications",   "🔔", "Notifications"),
        ("profile",         "👤", "Profile"),
    ],
    "admin": [
        ("dashboard",       "🏠", "Dashboard"),
        ("users",           "👥", "Users"),
        ("ai_monitoring",   "🤖", "AI Monitoring"),
        ("knowledge_base",  "📚", "Knowledge Base"),
        ("audit_logs",      "📜", "Audit Logs"),
        ("settings",        "⚙️",  "Settings"),
    ],
}


# ---------------------------------------------------------------------------
# Sidebar renderer
# ---------------------------------------------------------------------------

def render_sidebar(role: str, user: dict) -> str:
    """
    Render the role-aware sidebar navigation.
    Returns the current page key selected by the user.
    """
    nav_items = ROLE_NAV.get(role, [])
    role_label = ROLE_LABELS.get(role, role.title())

    # Brand + role chip
    st.sidebar.markdown(
        f'<div class="sidebar-logo">♻️ SwachhLoop AI</div><div class="sidebar-role-chip">{role_label}</div>',
        unsafe_allow_html=True,
    )

    # User greeting
    avatar = user.get('avatar_initials', '?')
    name = user.get('name', 'User')
    subtitle = user.get('ward', user.get('department', ''))
    st.sidebar.markdown(
        f'<div style="display:flex;align-items:center;gap:0.6rem;padding:0.6rem 0;margin-bottom:0.5rem;">'
        f'<div class="avatar">{avatar}</div>'
        f'<div>'
        f'<div style="font-weight:600;font-size:0.88rem;color:var(--text-primary);line-height:1.2;">{name}</div>'
        f'<div style="font-size:0.72rem;color:var(--text-secondary);">{subtitle}</div>'
        f'</div></div><div class="nav-separator"></div>',
        unsafe_allow_html=True,
    )

    # Navigation items
    current_page = st.session_state.get("current_page", nav_items[0][0] if nav_items else "dashboard")

    for page_key, icon, label in nav_items:
        is_active = current_page == page_key
        active_style = (
            "background:rgba(107,39,55,0.12);color:#6B2737;font-weight:600;"
            if is_active
            else "color:#5a5a7a;"
        )
        btn_clicked = st.sidebar.button(
            f"{icon}  {label}",
            key=f"nav_{page_key}",
            use_container_width=True,
        )
        if btn_clicked:
            st.session_state["current_page"] = page_key
            # Clear detail state when switching pages
            for k in ["selected_complaint", "selected_task", "report_success"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    # Separator + logout
    st.sidebar.markdown('<div class="nav-separator"></div>', unsafe_allow_html=True)
    if st.sidebar.button("🚪  Logout", key="sidebar_logout", use_container_width=True):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.rerun()

    st.sidebar.markdown(
        '<div class="text-muted" style="margin-top:1rem;font-size:0.7rem;">SwachhLoop AI v0.2.0 · Phase 2</div>',
        unsafe_allow_html=True,
    )

    return current_page


# ---------------------------------------------------------------------------
# Top bar renderer
# ---------------------------------------------------------------------------

def render_topbar(user: dict, role: str, page_title: str = "") -> None:
    """Render a glass top bar with brand, page title, and user info."""
    unread = _count_unread(role)
    notif_badge = (
        f'<span class="badge priority-critical" style="font-size:0.65rem;padding:0.15em 0.5em;">{unread}</span>'
        if unread > 0
        else ""
    )

    title_html = f'<span style="color:var(--text-muted);font-size:0.85rem;">/ {page_title}</span>' if page_title else ""
    user_name = user.get("name", "")
    avatar = user.get("avatar_initials", "?")

    html = (
        f'<div class="topbar">'
        f'<div style="display:flex;align-items:center;gap:0.75rem;">'
        f'<span class="topbar-brand">♻️ SwachhLoop AI</span>{title_html}'
        f'</div>'
        f'<div style="display:flex;align-items:center;gap:1.25rem;">'
        f'<div class="topbar-user">'
        f'<span style="color:var(--text-muted);font-size:0.78rem;">🔔 Notifications</span>{notif_badge}'
        f'</div>'
        f'<div style="display:flex;align-items:center;gap:0.5rem;">'
        f'<div class="avatar" style="width:30px;height:30px;font-size:0.7rem;">{avatar}</div>'
        f'<span class="topbar-user">{user_name}</span>'
        f'</div>'
        f'</div>'
        f'</div>'
    )

    st.markdown(html, unsafe_allow_html=True)


def _count_unread(role: str) -> int:
    """Count unread notifications for the top bar badge."""
    from frontend.services.api_client import get_notifications
    notifs = get_notifications(role)
    return sum(1 for n in notifs if not n.get("read", True))
