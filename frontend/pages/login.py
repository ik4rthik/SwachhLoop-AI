"""
SwachhLoop AI — Login Page
============================
Shared login page for all roles.

Phase 2: Demo/prototype authentication using DEMO_USERS list.
Phase 3: Replace authenticate_user() with real JWT authentication.
"""

import streamlit as st
from frontend.services.api_client import authenticate_user, get_demo_users


def render() -> None:
    """Render the shared SwachhLoop AI login page."""

    # Centre the login form
    _, centre, _ = st.columns([1, 1.4, 1])

    with centre:
        # Logo + heading
        st.markdown(
            """
            <div style="text-align:center;margin-bottom:2rem;">
                <div style="font-size:2.5rem;margin-bottom:0.5rem;">♻️</div>
                <div style="font-family:'Outfit',sans-serif;font-size:1.6rem;font-weight:700;color:#6B2737;">
                    SwachhLoop AI
                </div>
                <div style="font-size:0.85rem;color:#5a5a7a;margin-top:0.2rem;">
                    Sign in to your account
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        # Demo user quick-fill
        demo_users = get_demo_users()
        role_map = {u["role"]: u for u in demo_users}
        demo_labels = {
            "citizen":        "🏠 Citizen — Arjun Nair",
            "cleaner":        "🧹 Cleaner — Rajan Pillai",
            "municipal_staff": "🏛️ Municipal Staff — Priya Menon",
            "admin":          "⚙️ Admin — Dr. Suresh Kumar",
        }

        # Check if a role hint was passed from landing page
        hint_role = st.session_state.pop("login_hint_role", None) or st.session_state.pop("login_hint", None)
        default_demo_idx = 0
        if hint_role and hint_role in list(role_map.keys()):
            default_demo_idx = list(role_map.keys()).index(hint_role)

        selected_demo_label = st.selectbox(
            "Quick-fill demo account",
            options=list(demo_labels.values()),
            index=default_demo_idx,
            key="demo_user_select",
            help="Phase 2 demo mode. Select a role to auto-fill credentials.",
        )

        # Reverse map label → role key
        reverse_demo = {v: k for k, v in demo_labels.items()}
        chosen_role = reverse_demo.get(selected_demo_label, "citizen")
        chosen_user_data = role_map.get(chosen_role, demo_users[0])

        st.markdown('<hr class="styled">', unsafe_allow_html=True)

        # Login form
        with st.form("login_form"):
            email = st.text_input(
                "Email",
                value=chosen_user_data["email"],
                placeholder="you@example.com",
                key="login_email",
            )
            password = st.text_input(
                "Password",
                value="demo123",
                type="password",
                placeholder="Enter your password",
                key="login_password",
            )

            col1, col2 = st.columns([1, 1])
            with col1:
                submitted = st.form_submit_button(
                    "Sign In →",
                    use_container_width=True,
                    type="primary",
                )
            with col2:
                st.form_submit_button(
                    "Forgot Password",
                    use_container_width=True,
                    disabled=True,
                    help="Password reset available in Phase 3",
                )

        # Handle login
        if submitted:
            if not email or not password:
                st.error("Please enter both email and password.")
            else:
                user = authenticate_user(email.strip(), password)
                if user:
                    st.session_state["logged_in"] = True
                    st.session_state["user"] = user
                    st.session_state["role"] = user["role"]
                    st.session_state["current_page"] = "dashboard"
                    st.session_state["current_page_root"] = "app"
                    st.success(f"Welcome back, {user['name']}! Redirecting…")
                    st.rerun()
                else:
                    st.error("Invalid email or password. Try a demo account above.")

        st.markdown("</div>", unsafe_allow_html=True)

        # Register link
        st.markdown(
            """
            <div style="text-align:center;margin-top:1.25rem;font-size:0.83rem;color:#5a5a7a;">
                New to SwachhLoop AI?
                <span style="color:#6B2737;font-weight:600;cursor:pointer;">
                    Register (Phase 3)
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Demo note
        st.markdown(
            """
            <div class="glass-card" style="margin-top:1.5rem;padding:0.85rem 1rem;background:rgba(107,39,55,0.04);">
                <div style="font-size:0.75rem;font-weight:600;color:#6B2737;margin-bottom:0.3rem;">🔐 Phase 2 Demo Mode</div>
                <div class="text-muted">
                    All accounts use password: <code style="background:rgba(107,39,55,0.08);padding:0.1em 0.4em;border-radius:4px;">demo123</code><br>
                    Real authentication will be implemented in Phase 3.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Back to landing
    _, back_col, _ = st.columns([1, 1.4, 1])
    with back_col:
        if st.button("← Back to Home", key="back_to_landing"):
            st.session_state["current_page_root"] = "landing"
            st.rerun()
