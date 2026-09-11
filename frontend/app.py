"""
SwachhLoop AI — Streamlit Frontend Entry Point
===============================================
Run with:
    streamlit run frontend/app.py

This is the main entry point for the web application.
It handles role selection and routes users to the appropriate dashboard.

Architecture (Phase 1 — placeholder routing):
    app.py (this file)
        ├── pages/citizen.py
        ├── pages/cleaner.py
        ├── pages/municipal_staff.py
        └── pages/admin.py

Phase 2+: Replace the role dropdown with real authentication.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Page configuration — must be the FIRST Streamlit call
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SwachhLoop AI",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Inline CSS for basic branding
# ---------------------------------------------------------------------------
st.markdown(
    """
    <style>
        /* Center the landing card */
        .main-header {
            text-align: center;
            padding: 2rem 0 1rem;
        }
        .role-info {
            background: #f0f7f0;
            border-left: 4px solid #2e7d32;
            padding: 0.75rem 1rem;
            border-radius: 4px;
            margin: 0.5rem 0;
        }
        footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="main-header">'
    '<h1>♻️ SwachhLoop AI</h1>'
    "<p><em>Autonomous Multi-Agent System for Closed-Loop Smart Civic Waste Management</em></p>"
    "</div>",
    unsafe_allow_html=True,
)

st.divider()

# ---------------------------------------------------------------------------
# Sidebar — Role selection (Phase 1 placeholder for real auth in Phase 2)
# ---------------------------------------------------------------------------
st.sidebar.title("SwachhLoop AI")
st.sidebar.markdown("**Phase 1 — Foundation**")
st.sidebar.divider()

st.sidebar.markdown(
    "> ⚠️ **Note:** Role-based authentication is coming in Phase 2. "
    "For now, select your role below to preview the dashboard skeleton."
)
st.sidebar.divider()

ROLES = {
    "🏠  Citizen": "citizen",
    "🧹  Cleaner": "cleaner",
    "🏛️  Municipal Staff": "municipal_staff",
    "⚙️  Admin": "admin",
}

selected_label = st.sidebar.selectbox(
    "Select your role",
    options=list(ROLES.keys()),
    index=0,
)
selected_role = ROLES[selected_label]

# ---------------------------------------------------------------------------
# Route to the appropriate dashboard page
# ---------------------------------------------------------------------------
if selected_role == "citizen":
    from frontend.pages import citizen
    citizen.render()

elif selected_role == "cleaner":
    from frontend.pages import cleaner
    cleaner.render()

elif selected_role == "municipal_staff":
    from frontend.pages import municipal_staff
    municipal_staff.render()

elif selected_role == "admin":
    from frontend.pages import admin
    admin.render()

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.sidebar.divider()
st.sidebar.caption("SwachhLoop AI v0.1.0 — Phase 1 Foundation")
