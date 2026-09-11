"""
SwachhLoop AI — Citizen Dashboard
===================================
Phase 1: Structural placeholder only.
Phase 2: Complaint submission form, status tracking.
Phase 3: AI-assisted waste detection via camera upload.
"""

import streamlit as st


def render() -> None:
    """Render the Citizen Dashboard."""
    st.title("🏠 Citizen Dashboard")
    st.caption("Report waste, track complaints, and view resolution status.")

    st.info(
        "**Phase 2** will add:\n"
        "- Waste complaint submission form\n"
        "- Real-time complaint status tracker\n"
        "- Complaint history\n\n"
        "**Phase 3** will add:\n"
        "- AI-powered waste photo upload and classification\n"
        "- Automated urgency detection",
        icon="🚧",
    )

    # -----------------------------------------------------------------------
    # Placeholder UI layout — shows intended structure for Phase 2
    # -----------------------------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="My Complaints", value="—", delta=None)

    with col2:
        st.metric(label="Resolved", value="—", delta=None)

    with col3:
        st.metric(label="Pending", value="—", delta=None)

    st.divider()

    st.subheader("Report a Waste Issue")
    st.text_input("📍 Location / Address", placeholder="e.g. Near Gandhi Park, Ward 5", disabled=True)
    st.text_area("📝 Describe the issue", placeholder="Describe what you see...", disabled=True)
    st.file_uploader("📷 Upload a photo (optional)", type=["jpg", "jpeg", "png"], disabled=True)
    st.button("Submit Complaint", disabled=True)
    st.caption("_Complaint submission will be enabled in Phase 2._")
