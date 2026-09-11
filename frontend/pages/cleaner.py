"""
SwachhLoop AI — Cleaner Dashboard
====================================
Phase 1: Structural placeholder only.
Phase 2: Task list, status updates, proof-of-completion upload.
Phase 4: Optimized route display on map.
"""

import streamlit as st


def render() -> None:
    """Render the Cleaner Dashboard."""
    st.title("🧹 Cleaner Dashboard")
    st.caption("View assigned tasks, update status, and submit cleanup proof.")

    st.info(
        "**Phase 2** will add:\n"
        "- Assigned task list with priority indicators\n"
        "- Status update buttons (En Route / Cleaning / Done)\n"
        "- Before/after photo upload\n\n"
        "**Phase 4** will add:\n"
        "- Optimized route map using OR-Tools\n"
        "- Turn-by-turn navigation integration",
        icon="🚧",
    )

    # -----------------------------------------------------------------------
    # Placeholder UI layout
    # -----------------------------------------------------------------------
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(label="Tasks Today", value="—")

    with col2:
        st.metric(label="Completed", value="—")

    with col3:
        st.metric(label="Remaining", value="—")

    st.divider()

    st.subheader("Today's Assignments")
    st.markdown("_No tasks assigned yet. Task management will be enabled in Phase 2._")

    st.divider()

    st.subheader("Submit Cleanup Proof")
    st.file_uploader("📷 Upload before photo", type=["jpg", "jpeg", "png"], disabled=True)
    st.file_uploader("📷 Upload after photo", type=["jpg", "jpeg", "png"], disabled=True)
    st.button("Mark as Complete", disabled=True)
    st.caption("_Cleanup verification will be enabled in Phase 4._")
