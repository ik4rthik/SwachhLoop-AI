"""
SwachhLoop AI — Status Timeline Component
==========================================
Renders a vertical status timeline showing complaint/task progress.
"""

import streamlit as st


STEP_ORDER = [
    "SUBMITTED",
    "VALIDATED",
    "ASSIGNED",
    "CLEANING",
    "VERIFICATION",
    "RESOLVED",
]

STEP_ICONS = {
    "SUBMITTED":    "📋",
    "VALIDATED":    "✅",
    "ASSIGNED":     "👷",
    "CLEANING":     "🧹",
    "VERIFICATION": "🔍",
    "RESOLVED":     "🎉",
}


def render_timeline(steps: list[dict]) -> None:
    """
    Render a vertical status timeline.

    Args:
        steps: list of dicts with keys:
            step  (str)  — step name (e.g., "SUBMITTED")
            done  (bool) — whether this step is completed
            time  (str|None) — timestamp string or None
    """
    html_parts = ['<div class="timeline">']
    is_last = len(steps) - 1

    for i, step_data in enumerate(steps):
        step = step_data.get("step", "")
        done = step_data.get("done", False)
        time = step_data.get("time", None)
        icon = STEP_ICONS.get(step, "•")

        # Determine if this is the active (current) step
        is_active = (
            not done
            and i > 0
            and steps[i - 1].get("done", False)
        )

        dot_class = "done" if done else ("active" if is_active else "")
        label_class = "done" if done else ("pending" if not is_active else "")
        line_class = "done" if done else ""

        time_html = f'<div class="timeline-time">{time}</div>' if time else ""

        html_parts.append(f"""
        <div class="timeline-step">
            <div class="timeline-indicator">
                <div class="timeline-dot {dot_class}"></div>
                {"" if i == is_last else f'<div class="timeline-line {line_class}"></div>'}
            </div>
            <div class="timeline-content">
                <div class="timeline-label {label_class}">{icon} {step.replace("_", " ").title()}</div>
                {time_html}
            </div>
        </div>
        """)

    html_parts.append("</div>")
    st.markdown("".join(html_parts), unsafe_allow_html=True)
