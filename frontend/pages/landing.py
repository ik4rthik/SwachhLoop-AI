"""
SwachhLoop AI — Landing Page
===============================
Public-facing landing page. No authentication required.
"""

import streamlit as st


def render() -> None:
    """Render the SwachhLoop AI landing page."""

    # ── Top Bar ───────────────────────────────────────────────────────────
    top_col1, top_col2 = st.columns([5, 1])
    with top_col1:
        st.markdown(
            '<div style="font-family:\'Outfit\',sans-serif;font-size:1.35rem;font-weight:700;color:#6B2737;padding-top:0.4rem;">♻️ SwachhLoop AI</div>',
            unsafe_allow_html=True,
        )
    with top_col2:
        if st.button("Sign In →", key="landing_top_login_btn", type="primary", use_container_width=True):
            st.session_state["current_page_root"] = "login"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Hero Section ──────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="hero-section">
            <div style="display:inline-flex;align-items:center;gap:0.5rem;
                        background:rgba(107,39,55,0.08);border:1px solid rgba(107,39,55,0.2);
                        border-radius:9999px;padding:0.3em 1em;margin-bottom:1.5rem;
                        font-size:0.78rem;font-weight:600;color:#6B2737;letter-spacing:0.04em;">
                ♻️ &nbsp; AI-Powered Civic Waste Management
            </div>
            <h1 class="hero-title">
                Smarter Waste<br>for <span>Cleaner Communities</span>
            </h1>
            <p class="hero-subtitle">
                SwachhLoop AI closes the loop on civic waste management —
                from citizen reporting through AI-assisted validation,
                smart routing, and verified resolution.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── CTA Buttons ───────────────────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 1, 1, ])
    with col2:
        if st.button("📸  Report Waste", type="primary", use_container_width=True):
            st.session_state["goto_login"] = True
            st.session_state["login_hint"] = "citizen"
            st.rerun()
    with col3:
        if st.button("🔐  Sign In", use_container_width=True):
            st.session_state["current_page_root"] = "login"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Closed-loop concept strip ─────────────────────────────────────────
    st.markdown(
        """
        <div style="display:flex;align-items:center;justify-content:center;flex-wrap:wrap;gap:0.4rem;margin:0.5rem 0 2rem;padding:1rem;">
            <span class="loop-step">📋 Report</span>
            <span class="loop-arrow">→</span>
            <span class="loop-step">✅ Validate</span>
            <span class="loop-arrow">→</span>
            <span class="loop-step">👷 Assign</span>
            <span class="loop-arrow">→</span>
            <span class="loop-step">🧹 Collect</span>
            <span class="loop-arrow">→</span>
            <span class="loop-step">🔍 Verify</span>
            <span class="loop-arrow">→</span>
            <span class="loop-step">🎉 Resolve</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Feature Cards ─────────────────────────────────────────────────────
    st.markdown('<div class="section-title" style="text-align:center;font-size:1.3rem;">How SwachhLoop AI Works</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    fc1, fc2, fc3, fc4 = st.columns(4)

    features = [
        ("🤖", "AI Waste Detection", "Computer vision identifies waste type and urgency from photos — automatically."),
        ("🗺️", "Smart Routing", "Optimized cleanup routes save time and fuel for sanitation workers."),
        ("🔍", "Cleanup Verification", "Before/after image comparison confirms every cleanup is completed."),
        ("💡", "Civic Awareness", "Multilingual awareness content helps communities adopt better waste habits."),
    ]
    for col, (icon, title, desc) in zip([fc1, fc2, fc3, fc4], features):
        with col:
            st.markdown(
                f"""
                <div class="feature-card">
                    <div class="feature-icon">{icon}</div>
                    <div class="feature-title">{title}</div>
                    <div class="feature-desc">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Stats strip ───────────────────────────────────────────────────────
    st.markdown(
        """
        <div class="glass-card" style="text-align:center;">
            <div style="display:flex;justify-content:space-around;flex-wrap:wrap;gap:1.5rem;">
                <div>
                    <div style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:700;color:#6B2737;">128+</div>
                    <div style="font-size:0.8rem;color:#5a5a7a;font-weight:500;">Complaints Resolved</div>
                </div>
                <div>
                    <div style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:700;color:#2d6a4f;">8</div>
                    <div style="font-size:0.8rem;color:#5a5a7a;font-weight:500;">Active Cleaners</div>
                </div>
                <div>
                    <div style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:700;color:#1565c0;">18.4h</div>
                    <div style="font-size:0.8rem;color:#5a5a7a;font-weight:500;">Avg. Resolution Time</div>
                </div>
                <div>
                    <div style="font-family:'Outfit',sans-serif;font-size:2rem;font-weight:700;color:#6B2737;">7</div>
                    <div style="font-size:0.8rem;color:#5a5a7a;font-weight:500;">Wards Covered</div>
                </div>
            </div>
            <div class="text-muted" style="margin-top:0.75rem;">Phase 2 demo data · Real data in Phase 3</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Role cards ────────────────────────────────────────────────────────
    st.markdown('<div class="section-title" style="text-align:center;font-size:1.3rem;">Built for Every Stakeholder</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    rc1, rc2, rc3, rc4 = st.columns(4)
    roles = [
        ("🏠", "Citizens", "Report waste issues instantly with photos. Track your complaints to resolution.", "citizen"),
        ("🧹", "Cleaners", "Receive optimized task assignments and submit verified cleanup proof.", "cleaner"),
        ("🏛️", "Municipal Staff", "Oversee the full pipeline — validate, assign, monitor, and escalate.", "municipal_staff"),
        ("⚙️", "Admins", "Manage users, monitor AI services, and keep the system running smoothly.", "admin"),
    ]
    for col, (icon, title, desc, role_key) in zip([rc1, rc2, rc3, rc4], roles):
        with col:
            clicked = st.button(f"{icon} {title}", key=f"role_cta_{role_key}", use_container_width=True, type="secondary")
            st.markdown(f'<div class="text-muted" style="font-size:0.78rem;text-align:center;padding:0.25rem 0;">{desc}</div>', unsafe_allow_html=True)
            if clicked:
                st.session_state["current_page_root"] = "login"
                st.session_state["login_hint_role"] = role_key
                st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    # ── Footer ────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="text-align:center;padding:2rem 0;border-top:1px solid rgba(107,39,55,0.08);">
            <div style="font-family:'Outfit',sans-serif;font-size:1rem;font-weight:700;color:#6B2737;margin-bottom:0.4rem;">♻️ SwachhLoop AI</div>
            <div class="text-muted">An Autonomous Multi-Agent System for Closed-Loop Smart Civic Waste Management</div>
            <div class="text-muted" style="margin-top:0.3rem;">Phase 2 · Frontend Prototype · Thrissur, Kerala</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
