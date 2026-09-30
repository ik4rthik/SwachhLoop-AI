"""
SwachhLoop AI — Notification Widget Component
==============================================
Renders notification cards for any role.
"""

import streamlit as st


def render_notifications(notifications: list[dict], role: str = "") -> None:
    """
    Render a list of notification cards.

    Args:
        notifications: List of notification dicts from api_client.get_notifications()
        role: User role string for context
    """
    unread = [n for n in notifications if not n.get("read", True)]
    read = [n for n in notifications if n.get("read", True)]

    unread_count = len(unread)

    # Header
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
            <div class="page-title">🔔 Notifications</div>
            {f'<span class="badge priority-critical">{unread_count} New</span>' if unread_count else ''}
        </div>
        <p class="page-subtitle">Stay updated on your complaints, tasks, and system alerts.</p>
        """,
        unsafe_allow_html=True,
    )

    if not notifications:
        st.markdown(
            """
            <div class="glass-card" style="text-align:center;padding:3rem;">
                <div style="font-size:2.5rem;margin-bottom:0.5rem;">🔕</div>
                <div style="font-weight:600;color:var(--text-secondary);">No notifications yet</div>
                <div class="text-muted">You're all caught up!</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    if unread:
        st.markdown('<div class="section-title">New</div>', unsafe_allow_html=True)
        for notif in unread:
            _render_notif_card(notif)

    if read:
        st.markdown('<div class="section-title">Earlier</div>', unsafe_allow_html=True)
        for notif in read:
            _render_notif_card(notif)


def _render_notif_card(notif: dict) -> None:
    notif_type = notif.get("type", "info")
    is_unread = not notif.get("read", True)

    type_icons = {
        "success": "✅",
        "info": "ℹ️",
        "warning": "⚠️",
        "error": "🚨",
    }
    icon = type_icons.get(notif_type, "•")
    unread_class = "unread" if is_unread else ""

    st.markdown(
        f"""
        <div class="notif-card {unread_class}">
            <div class="notif-dot {notif_type}" style="margin-top:0.4rem;"></div>
            <div style="flex:1;">
                <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem;">
                    <div style="font-weight:600;font-size:0.88rem;color:var(--text-primary);">{icon} {notif['title']}</div>
                    <div class="text-muted" style="white-space:nowrap;">{notif.get('time','')}</div>
                </div>
                <div style="font-size:0.82rem;color:var(--text-secondary);margin-top:0.2rem;">{notif['message']}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
