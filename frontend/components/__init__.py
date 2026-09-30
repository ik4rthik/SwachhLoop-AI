"""
SwachhLoop AI — Shared Components Package
==========================================
Exports all reusable UI components.

Phase 2 Components:
    Design System:
        inject_css          — injects global CSS design tokens

    Layout:
        render_sidebar      — role-aware sidebar navigation
        render_topbar       — glass top navigation bar

    Cards:
        stat_card           — KPI metric card
        complaint_card      — complaint list item
        task_card           — cleaner task list item
        ai_assessment_card  — AI analysis result block

    Badges:
        status_badge_html   — HTML string for status badge
        priority_badge_html — HTML string for priority badge
        render_status_badge — renders status badge via st.markdown
        render_priority_badge — renders priority badge via st.markdown
        render_badge_row    — renders both badges side by side

    Timeline:
        render_timeline     — vertical status timeline

    Map:
        render_map          — prototype map with markers

    Notifications:
        render_notifications — notification card list
"""

from frontend.components.design_system import inject_css
from frontend.components.layout import render_sidebar, render_topbar
from frontend.components.cards import (
    stat_card,
    complaint_card,
    task_card,
    ai_assessment_card,
)
from frontend.components.badges import (
    status_badge_html,
    priority_badge_html,
    render_status_badge,
    render_priority_badge,
    render_badge_row,
)
from frontend.components.timeline import render_timeline
from frontend.components.map_widget import render_map
from frontend.components.notifications_widget import render_notifications

__all__ = [
    "inject_css",
    "render_sidebar",
    "render_topbar",
    "stat_card",
    "complaint_card",
    "task_card",
    "ai_assessment_card",
    "status_badge_html",
    "priority_badge_html",
    "render_status_badge",
    "render_priority_badge",
    "render_badge_row",
    "render_timeline",
    "render_map",
    "render_notifications",
]
