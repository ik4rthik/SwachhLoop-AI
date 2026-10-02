"""
SwachhLoop AI — Shared UI Components: Cards
=============================================
GlassCard, StatCard, ComplaintCard, TaskCard
"""

import textwrap
import streamlit as st


# ---------------------------------------------------------------------------
# Glass Card wrapper
# ---------------------------------------------------------------------------

def glass_card_open(title: str | None = None, icon: str | None = None) -> None:
    """Open a glass card container (use with st.container())."""
    header = ""
    if title:
        icon_html = f'<span style="margin-right:0.4rem;">{icon}</span>' if icon else ""
        header = f'<div class="section-title" style="margin-top:0">{icon_html}{title}</div>'
    st.markdown(f'<div class="glass-card">{header}', unsafe_allow_html=True)


def glass_card_close() -> None:
    st.markdown('</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Stat Card
# ---------------------------------------------------------------------------

def stat_card(
    label: str,
    value: str | int,
    icon: str = "",
    variant: str = "default",  # "default" | "brand" | "success" | "critical" | "warning"
    delta: str | None = None,
) -> None:
    """Render a glassmorphic KPI stat card."""
    delta_html = ""
    if delta:
        delta_html = f'<div class="text-muted" style="margin-top:0.25rem;font-size:0.78rem;">{delta}</div>'

    st.markdown(
        textwrap.dedent(f"""
        <div class="stat-card {variant}">
            <div class="stat-icon">{icon}</div>
            <div class="stat-value">{value}</div>
            <div class="stat-label">{label}</div>
            {delta_html}
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Complaint Card
# ---------------------------------------------------------------------------

def complaint_card(complaint: dict, show_action: bool = True, action_label: str = "View Details") -> bool:
    """
    Render a compact complaint list card.
    Returns True if the action button was clicked.
    """
    from frontend.components.badges import status_badge_html, priority_badge_html

    status_html = status_badge_html(complaint.get("status", "SUBMITTED"))
    priority_html = priority_badge_html(complaint.get("priority", "LOW"))
    cleaner = complaint.get("assigned_cleaner", None)
    cleaner_html = f"<span>👷 {cleaner}</span>" if cleaner else "<span>Unassigned</span>"

    st.markdown(
        textwrap.dedent(f"""
        <div class="complaint-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem;flex-wrap:wrap;">
                <div>
                    <div class="complaint-card-id">{complaint['id']}</div>
                    <div class="complaint-card-title">{complaint['title']}</div>
                    <div class="complaint-card-meta" style="margin-top:0.3rem;display:flex;gap:0.75rem;flex-wrap:wrap;align-items:center;">
                        <span>📍 {complaint['location']}</span>
                        <span>🕐 {complaint['reported_at']}</span>
                        {cleaner_html}
                    </div>
                </div>
                <div style="display:flex;flex-direction:column;align-items:flex-end;gap:0.3rem;flex-shrink:0;">
                    {priority_html}
                    {status_html}
                </div>
            </div>
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )

    if show_action:
        clicked = st.button(action_label, key=f"btn_{complaint['id']}_{action_label}", type="primary")
        return clicked
    return False


# ---------------------------------------------------------------------------
# Task Card (Cleaner)
# ---------------------------------------------------------------------------

def task_card(task: dict) -> bool:
    """
    Render a cleaner task card.
    Returns True if View Task is clicked.
    """
    from frontend.components.badges import status_badge_html, priority_badge_html

    priority_html = priority_badge_html(task.get("priority", "LOW"))
    status_html = status_badge_html(task.get("status", "PENDING"))

    priority_border_color = {
        "CRITICAL": "#c62828",
        "HIGH": "#e65100",
        "MEDIUM": "#f57f17",
        "LOW": "#2d6a4f",
    }.get(task.get("priority", "LOW"), "#9090a8")

    st.markdown(
        textwrap.dedent(f"""
        <div class="complaint-card" style="border-left: 4px solid {priority_border_color};">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:0.5rem;flex-wrap:wrap;">
                <div>
                    <div class="complaint-card-id">{task['id']} · {task['complaint_id']}</div>
                    <div class="complaint-card-title">{task['title']}</div>
                    <div class="complaint-card-meta" style="margin-top:0.3rem;display:flex;gap:0.75rem;flex-wrap:wrap;align-items:center;">
                        <span>📍 {task['location']}</span>
                        <span>🗺️ {task['distance']}</span>
                        <span>⏱️ Est. {task['estimated_time']}</span>
                        <span>🗑️ {task['waste_type']}</span>
                    </div>
                </div>
                <div style="display:flex;flex-direction:column;align-items:flex-end;gap:0.3rem;flex-shrink:0;">
                    {priority_html}
                    {status_html}
                </div>
            </div>
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([3, 1])
    with col2:
        clicked = st.button("View Task →", key=f"task_btn_{task['id']}", type="primary")
    return clicked


# ---------------------------------------------------------------------------
# AI Assessment Card (Municipal Staff / Detail)
# ---------------------------------------------------------------------------

def ai_assessment_card(
    waste_type: str,
    confidence: int,
    priority: str,
    reason: str,
) -> None:
    """Render the AI assessment summary block."""
    priority_color = {
        "CRITICAL": "#c62828",
        "HIGH": "#e65100",
        "MEDIUM": "#f57f17",
        "LOW": "#2d6a4f",
    }.get(priority.upper(), "#9090a8")

    st.markdown(
        textwrap.dedent(f"""
        <div class="ai-badge" style="margin-bottom:1rem;">
            <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.75rem;">
                <span style="font-size:1.1rem;">🤖</span>
                <span class="ai-badge-label">AI Assessment</span>
                <span style="font-size:0.68rem;color:#9090a8;margin-left:auto;">Demo values · Phase 3 will use real AI</span>
            </div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;">
                <div>
                    <div class="ai-badge-label">Waste Type</div>
                    <div class="ai-badge-value">{waste_type}</div>
                </div>
                <div>
                    <div class="ai-badge-label">Confidence</div>
                    <div class="ai-badge-value">{confidence}%</div>
                </div>
                <div>
                    <div class="ai-badge-label">Priority</div>
                    <div class="ai-badge-value" style="color:{priority_color};">{priority}</div>
                </div>
            </div>
            <div style="margin-top:0.75rem;padding-top:0.75rem;border-top:1px solid rgba(107,39,55,0.10);">
                <div class="ai-badge-label">Reason</div>
                <div style="font-size:0.85rem;color:var(--text-secondary);margin-top:0.2rem;">{reason}</div>
            </div>
        </div>
        """).strip(),
        unsafe_allow_html=True,
    )
