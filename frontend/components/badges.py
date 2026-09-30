"""
SwachhLoop AI — Status & Priority Badges
==========================================
Returns HTML badge strings and renders them via st.markdown.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Color maps
# ---------------------------------------------------------------------------

STATUS_MAP = {
    "SUBMITTED":    ("badge-submitted",    "Submitted"),
    "VALIDATED":    ("badge-validated",    "Validated"),
    "ASSIGNED":     ("badge-assigned",     "Assigned"),
    "CLEANING":     ("badge-cleaning",     "Cleaning"),
    "VERIFICATION": ("badge-verification", "Verification"),
    "RESOLVED":     ("badge-resolved",     "Resolved ✓"),
    "ESCALATED":    ("badge-escalated",    "Escalated ⚠"),
    "PENDING":      ("badge-pending",      "Pending"),
    "IN_PROGRESS":  ("badge-in-progress",  "In Progress"),
    "COMPLETED":    ("badge-completed",    "Completed ✓"),
}

PRIORITY_MAP = {
    "CRITICAL": ("priority-critical", "🔴 Critical"),
    "HIGH":     ("priority-high",     "🟠 High"),
    "MEDIUM":   ("priority-medium",   "🟡 Medium"),
    "LOW":      ("priority-low",      "🟢 Low"),
}


# ---------------------------------------------------------------------------
# HTML helpers (for use inside card HTML strings)
# ---------------------------------------------------------------------------

def status_badge_html(status: str) -> str:
    cls, label = STATUS_MAP.get(status.upper(), ("badge-submitted", status))
    return f'<span class="badge {cls}">{label}</span>'


def priority_badge_html(priority: str) -> str:
    cls, label = PRIORITY_MAP.get(priority.upper(), ("priority-low", priority))
    return f'<span class="badge {cls}">{label}</span>'


# ---------------------------------------------------------------------------
# Streamlit render helpers
# ---------------------------------------------------------------------------

def render_status_badge(status: str) -> None:
    """Render a status badge inline via st.markdown."""
    st.markdown(status_badge_html(status), unsafe_allow_html=True)


def render_priority_badge(priority: str) -> None:
    """Render a priority badge inline via st.markdown."""
    st.markdown(priority_badge_html(priority), unsafe_allow_html=True)


def render_badge_row(status: str, priority: str) -> None:
    """Render both badges side by side."""
    st.markdown(
        f'<div style="display:flex;gap:0.4rem;flex-wrap:wrap;margin:0.3rem 0;">'
        f'{priority_badge_html(priority)}'
        f'{status_badge_html(status)}'
        f'</div>',
        unsafe_allow_html=True,
    )
