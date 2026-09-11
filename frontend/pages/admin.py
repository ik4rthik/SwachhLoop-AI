"""
SwachhLoop AI — Admin Dashboard
=================================
Phase 1: Structural placeholder only.
Phase 2: User management, system configuration.
Phase 3+: AI system monitoring, model metrics, agent logs.
"""

import streamlit as st


def render() -> None:
    """Render the Admin Dashboard."""
    st.title("⚙️ Admin Dashboard")
    st.caption("System administration, user management, and AI monitoring.")

    st.info(
        "**Phase 2** will add:\n"
        "- User account management (create, deactivate, assign roles)\n"
        "- Ward / Zone configuration\n\n"
        "**Phase 3+** will add:\n"
        "- AI service health monitoring\n"
        "- Agent execution logs (LangGraph traces)\n"
        "- Model performance metrics\n"
        "- Guardrail violation reports",
        icon="🚧",
    )

    # -----------------------------------------------------------------------
    # Placeholder UI layout
    # -----------------------------------------------------------------------
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(label="Total Users", value="—")

    with col2:
        st.metric(label="Active Cleaners", value="—")

    with col3:
        st.metric(label="Wards Covered", value="—")

    with col4:
        st.metric(label="AI Services", value="—")

    st.divider()

    # API health check widget
    st.subheader("🔌 Backend API Status")

    import httpx  # imported here to avoid circular import at module level
    import os

    api_url = os.environ.get("API_BASE_URL", "http://localhost:8000")

    if st.button("Check API Health"):
        try:
            response = httpx.get(f"{api_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                st.success(
                    f"✅ **API is online**  \n"
                    f"Status: `{data.get('status')}`  |  "
                    f"Version: `{data.get('version')}`  |  "
                    f"Env: `{data.get('environment')}`"
                )
            else:
                st.error(f"❌ API returned HTTP {response.status_code}")
        except Exception as exc:
            st.error(f"❌ Cannot reach API at `{api_url}`: {exc}")

    st.caption(f"_API URL: `{api_url}`_")

    st.divider()

    st.subheader("User Management")
    st.markdown("_User management will be enabled in Phase 2._")
