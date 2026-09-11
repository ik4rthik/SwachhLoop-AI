"""
SwachhLoop AI — Municipal Staff Dashboard
==========================================
Phase 1: Structural placeholder only.
Phase 2: Complaint queue management, task assignment to cleaners.
Phase 3: AI-assisted complaint analysis, urgency triage.
"""

import streamlit as st


def render() -> None:
    """Render the Municipal Staff Dashboard."""
    st.title("🏛️ Municipal Staff Dashboard")
    st.caption("Review complaints, assign cleanup tasks, and track resolution progress.")

    st.info(
        "**Phase 2** will add:\n"
        "- Incoming complaint queue\n"
        "- Assign cleaner to complaint\n"
        "- Status overview by ward/zone\n\n"
        "**Phase 3** will add:\n"
        "- AI urgency triage and auto-tagging\n"
        "- Complaint category analytics\n"
        "- Self-Corrective RAG for policy lookups",
        icon="🚧",
    )

    # -----------------------------------------------------------------------
    # Placeholder UI layout
    # -----------------------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Open Complaints", value="—")

    with col2:
        st.metric(label="In Progress", value="—")

    with col3:
        st.metric(label="Resolved Today", value="—")

    with col4:
        st.metric(label="Avg. Resolution Time", value="—")

    st.divider()

    st.subheader("Complaint Queue")
    st.markdown("_Complaint management will be enabled in Phase 2._")

    st.divider()

    st.subheader("Assign Task")
    st.selectbox("Select Complaint", options=["—"], disabled=True)
    st.selectbox("Assign to Cleaner", options=["—"], disabled=True)
    st.button("Assign", disabled=True)
