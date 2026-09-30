"""
SwachhLoop AI — Citizen Dashboard & Sub-pages
===============================================
Phase 2: Full prototype with mock data.
Phase 3: Connect to real API via frontend/services/api_client.py

Sub-pages:
    dashboard       — Overview, stats, recent complaints, map, awareness
    report_waste    — Waste complaint submission form
    my_complaints   — Complaint history list
    nearby_issues   — Map of nearby waste reports
    awareness       — Civic awareness content
    notifications   — Notification feed
    profile         — User profile
"""

import streamlit as st
import datetime

from frontend.components import (
    render_topbar, stat_card, complaint_card,
    render_timeline, render_map, render_notifications,
    status_badge_html, priority_badge_html,
)
from frontend.components.cards import ai_assessment_card
from frontend.services.api_client import (
    get_complaints, get_complaint_by_id, submit_complaint,
    get_notifications, get_map_markers, get_awareness_content,
)


def render() -> None:
    """Entry point — routes to the appropriate citizen sub-page."""
    user = st.session_state.get("user", {})
    current_page = st.session_state.get("current_page", "dashboard")

    render_topbar(user, "citizen", current_page.replace("_", " ").title())

    # Sub-page routing
    if "selected_complaint" in st.session_state:
        _render_complaint_detail(st.session_state["selected_complaint"])
    elif current_page == "dashboard":
        _render_dashboard(user)
    elif current_page == "report_waste":
        _render_report_waste(user)
    elif current_page == "my_complaints":
        _render_my_complaints(user)
    elif current_page == "nearby_issues":
        _render_nearby_issues()
    elif current_page == "awareness":
        _render_awareness()
    elif current_page == "notifications":
        render_notifications(get_notifications("citizen"), "citizen")
    elif current_page == "profile":
        _render_profile(user)
    else:
        _render_dashboard(user)


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

def _render_dashboard(user: dict) -> None:
    name = user.get("name", "").split()[0]
    complaints = get_complaints(citizen_id=user.get("id", "u001"))

    total = len(complaints)
    resolved = sum(1 for c in complaints if c["status"] == "RESOLVED")
    in_progress = sum(1 for c in complaints if c["status"] not in ("RESOLVED", "SUBMITTED"))
    pending = sum(1 for c in complaints if c["status"] == "SUBMITTED")

    # Greeting
    c_greet, c_action = st.columns([3, 1])
    with c_greet:
        st.markdown(
            f"""
            <div class="glass-card" style="padding:1.25rem 1.5rem;margin-bottom:1.25rem;">
                <div class="page-title">Hello, {name} 👋</div>
                <div class="page-subtitle">Here's your waste management summary for today.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c_action:
        st.markdown('<div style="height:0.8rem;"></div>', unsafe_allow_html=True)
        if st.button("📸  Report Waste", type="primary", key="hero_report_btn", use_container_width=True):
            st.session_state["current_page"] = "report_waste"
            st.rerun()

    # KPI stats
    c1, c2, c3, c4 = st.columns(4)
    with c1: stat_card("Total Reports", total, "📋", "brand")
    with c2: stat_card("In Progress", in_progress, "🔄", "warning")
    with c3: stat_card("Resolved", resolved, "✅", "success")
    with c4: stat_card("Pending Review", pending, "⏳", "default")

    st.markdown("<br>", unsafe_allow_html=True)

    # Two-column layout: recent complaints + map
    left, right = st.columns([1.1, 1])

    with left:
        st.markdown('<div class="section-title">📋 Recent Complaints</div>', unsafe_allow_html=True)
        recent = complaints[:3]
        if not recent:
            st.markdown(
                '<div class="glass-card" style="text-align:center;color:var(--text-muted);padding:2rem;">No complaints yet. Report one!</div>',
                unsafe_allow_html=True,
            )
        for c in recent:
            clicked = complaint_card(c, show_action=True, action_label="View Details")
            if clicked:
                st.session_state["selected_complaint"] = c["id"]
                st.rerun()

        if st.button("View All Complaints →", key="view_all_complaints"):
            st.session_state["current_page"] = "my_complaints"
            st.rerun()

    with right:
        st.markdown('<div class="section-title">📍 Nearby Waste Issues</div>', unsafe_allow_html=True)
        markers = get_map_markers()
        render_map(markers, height=250, show_legend=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="glass-card" style="padding:1rem;background:rgba(45,106,79,0.06);border-color:rgba(45,106,79,0.2);">
                <div style="font-size:0.8rem;font-weight:600;color:#2d6a4f;margin-bottom:0.3rem;">💡 Awareness Tip</div>
                <div style="font-size:0.82rem;color:#5a5a7a;">Segregate your waste into wet, dry, and hazardous categories before disposal.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # Impact section
    st.markdown(
        f"""
        <div class="glass-card" style="background:linear-gradient(135deg,rgba(107,39,55,0.05) 0%,rgba(45,106,79,0.05) 100%);">
            <div class="section-title" style="margin-top:0;">🌱 Your Environmental Impact</div>
            <div style="display:flex;gap:2rem;flex-wrap:wrap;">
                <div style="text-align:center;">
                    <div style="font-family:'Outfit',sans-serif;font-size:1.8rem;font-weight:700;color:#6B2737;">{resolved}</div>
                    <div style="font-size:0.75rem;color:#5a5a7a;font-weight:500;">Cleanups Triggered</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-family:'Outfit',sans-serif;font-size:1.8rem;font-weight:700;color:#2d6a4f;">{resolved * 12}</div>
                    <div style="font-size:0.75rem;color:#5a5a7a;font-weight:500;">kg Waste Removed (est.)</div>
                </div>
                <div style="text-align:center;">
                    <div style="font-family:'Outfit',sans-serif;font-size:1.8rem;font-weight:700;color:#1565c0;">{total}</div>
                    <div style="font-size:0.75rem;color:#5a5a7a;font-weight:500;">Reports Submitted</div>
                </div>
            </div>
            <div class="text-muted" style="margin-top:0.5rem;">Estimated values · Phase 3 will track real impact data</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Report Waste
# ---------------------------------------------------------------------------

def _render_report_waste(user: dict) -> None:
    # Success state
    if st.session_state.get("report_success"):
        result = st.session_state["report_result"]
        st.markdown(
            f"""
            <div class="success-banner">
                <div class="success-icon">✅</div>
                <div class="success-title">Report Submitted Successfully!</div>
                <div style="color:#5a5a7a;margin-top:0.5rem;font-size:0.9rem;">
                    Your waste report has been received. Municipal staff will validate it shortly.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Receipt card
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(
                f"""
                <div class="glass-card">
                    <div class="section-title" style="margin-top:0;">📋 Report Summary</div>
                    <div style="display:grid;grid-template-columns:auto 1fr;gap:0.4rem 1rem;font-size:0.85rem;">
                        <span style="color:var(--text-muted);font-weight:500;">Complaint ID</span>
                        <span class="mono" style="font-weight:600;color:var(--brand);">{result['complaint_id']}</span>
                        <span style="color:var(--text-muted);font-weight:500;">Status</span>
                        <span>{status_badge_html('SUBMITTED')}</span>
                        <span style="color:var(--text-muted);font-weight:500;">Location</span>
                        <span>{st.session_state.get('report_location','—')}</span>
                        <span style="color:var(--text-muted);font-weight:500;">Reported</span>
                        <span>{datetime.datetime.now().strftime('%b %d, %Y %I:%M %p')}</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                """
                <div class="glass-card" style="background:rgba(45,106,79,0.05);border-color:rgba(45,106,79,0.2);">
                    <div class="section-title" style="margin-top:0;color:#2d6a4f;">⏭ What happens next?</div>
                    <ol style="font-size:0.83rem;color:#5a5a7a;padding-left:1.2rem;line-height:2;">
                        <li>Municipal staff validates your report</li>
                        <li>AI assesses waste type &amp; priority</li>
                        <li>A cleaner is assigned to the task</li>
                        <li>Cleanup is performed &amp; verified</li>
                        <li>You receive a resolution notification</li>
                    </ol>
                </div>
                """,
                unsafe_allow_html=True,
            )

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("📸 Report Another Issue", type="primary", use_container_width=True):
                del st.session_state["report_success"]
                del st.session_state["report_result"]
                st.rerun()
        with col_b:
            if st.button("📋 View My Complaints", use_container_width=True):
                del st.session_state["report_success"]
                del st.session_state["report_result"]
                st.session_state["current_page"] = "my_complaints"
                st.rerun()
        return

    # Form
    st.markdown(
        """
        <div class="page-title">📸 Report Waste</div>
        <p class="page-subtitle">Submit a waste complaint. Our team will validate and assign a cleanup crew.</p>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    f_col, hint_col = st.columns([1.5, 1])

    with f_col:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "📷 Upload Waste Photo (optional)",
            type=["jpg", "jpeg", "png", "webp"],
            key="report_image",
            help="A photo helps AI detect waste type and urgency more accurately.",
        )

        if uploaded_file:
            st.image(uploaded_file, caption="Preview — this photo will be attached to your report", use_container_width=True)
            st.markdown(
                '<div class="text-muted" style="font-size:0.78rem;">📌 Phase 3: AI waste detection will analyse this image automatically.</div>',
                unsafe_allow_html=True,
            )

        location = st.text_input(
            "📍 Location / Address *",
            placeholder="e.g. Near Gandhi Park Gate, Ward 7, Thrissur",
            key="report_location_input",
        )

        use_current = st.checkbox(
            "📡 Use my current location",
            key="use_current_location",
            help="Phase 3: Will use device GPS automatically.",
        )
        if use_current:
            st.info("📍 Current location: Thrissur, Ward 7 (demo coordinates — real GPS in Phase 3)", icon="📡")
            if not location:
                location = "Thrissur, Ward 7 (GPS)"

        waste_type = st.selectbox(
            "🗑️ Waste Type",
            options=[
                "Not Sure (AI will classify)",
                "Mixed Municipal Waste",
                "Plastic Waste",
                "Organic / Food Waste",
                "Construction Debris",
                "Biomedical Waste",
                "Electronic Waste",
                "Hazardous Waste",
                "Other",
            ],
            key="report_waste_type",
        )

        description = st.text_area(
            "📝 Describe the Issue *",
            placeholder="Describe what you see — quantity, exact location details, any health hazard indicators…",
            height=120,
            key="report_description",
        )

        st.markdown("</div>", unsafe_allow_html=True)

        col_sub, col_can = st.columns([1, 1])
        with col_sub:
            submitted = st.button("📤  Submit Report", type="primary", use_container_width=True)
        with col_can:
            if st.button("← Cancel", use_container_width=True):
                st.session_state["current_page"] = "dashboard"
                st.rerun()

        if submitted:
            if not location or not description:
                st.error("Please fill in Location and Description before submitting.")
            else:
                result = submit_complaint({
                    "citizen_id": user.get("id"),
                    "location": location,
                    "description": description,
                    "waste_type": waste_type,
                    "image": uploaded_file is not None,
                })
                st.session_state["report_success"] = True
                st.session_state["report_result"] = result
                st.session_state["report_location"] = location
                st.rerun()

    with hint_col:
        st.markdown(
            """
            <div class="glass-card" style="padding:1.25rem;">
                <div class="section-title" style="margin-top:0;">💡 Tips for a Good Report</div>
                <ul style="font-size:0.82rem;color:#5a5a7a;line-height:2;padding-left:1.2rem;">
                    <li>Take a clear photo of the waste</li>
                    <li>Be specific about the location</li>
                    <li>Mention any health or safety hazards</li>
                    <li>Describe quantity (small, medium, large pile)</li>
                    <li>Note if waste is blocking roads or drains</li>
                </ul>
            </div>

            <div class="glass-card" style="margin-top:0.75rem;background:rgba(107,39,55,0.04);padding:1rem;">
                <div style="font-size:0.78rem;font-weight:600;color:#6B2737;margin-bottom:0.3rem;">🤖 AI Processing</div>
                <div class="text-muted">
                    In <strong>Phase 3</strong>, your photo will be automatically
                    analysed by AI to detect waste type, estimate quantity,
                    and assign a priority score — instantly.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# My Complaints
# ---------------------------------------------------------------------------

def _render_my_complaints(user: dict) -> None:
    st.markdown(
        '<div class="page-title">📋 My Complaints</div>'
        '<p class="page-subtitle">All waste reports submitted by you.</p>',
        unsafe_allow_html=True,
    )

    complaints = get_complaints(citizen_id=user.get("id", "u001"))

    # Filter bar
    status_filter = st.selectbox(
        "Filter by status",
        options=["All", "SUBMITTED", "VALIDATED", "ASSIGNED", "CLEANING", "VERIFICATION", "RESOLVED"],
        key="my_complaints_filter",
        label_visibility="collapsed",
    )

    st.markdown("<br>", unsafe_allow_html=True)

    filtered = [c for c in complaints if status_filter == "All" or c["status"] == status_filter]

    if not filtered:
        st.markdown(
            '<div class="glass-card" style="text-align:center;padding:3rem;color:var(--text-muted);">No complaints found. <br>Try a different filter or submit a new report.</div>',
            unsafe_allow_html=True,
        )
    else:
        for c in filtered:
            clicked = complaint_card(c, show_action=True, action_label="View Details")
            if clicked:
                st.session_state["selected_complaint"] = c["id"]
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("📸 Report New Issue", type="primary"):
        st.session_state["current_page"] = "report_waste"
        st.rerun()


# ---------------------------------------------------------------------------
# Complaint Detail
# ---------------------------------------------------------------------------

def _render_complaint_detail(complaint_id: str) -> None:
    complaint = get_complaint_by_id(complaint_id)

    if not complaint:
        st.error(f"Complaint {complaint_id} not found.")
        if st.button("← Back"):
            del st.session_state["selected_complaint"]
            st.rerun()
        return

    if st.button("← Back to Complaints", key="back_from_detail"):
        del st.session_state["selected_complaint"]
        st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # Header
    st.markdown(
        f"""
        <div class="glass-card">
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:0.75rem;">
                <div>
                    <div class="complaint-card-id">{complaint['id']}</div>
                    <div class="page-title" style="font-size:1.4rem;">{complaint['title']}</div>
                    <div class="page-subtitle">📍 {complaint['location']}</div>
                    <div class="page-subtitle">🕐 Reported: {complaint['reported_at']}</div>
                </div>
                <div style="display:flex;flex-direction:column;gap:0.4rem;align-items:flex-end;">
                    {priority_badge_html(complaint['priority'])}
                    {status_badge_html(complaint['status'])}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns([1, 1])

    with left:
        # Description
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title" style="margin-top:0;">📝 Description</div>
                <div style="font-size:0.88rem;color:var(--text-secondary);line-height:1.7;">
                    {complaint.get('description', '—')}
                </div>
                <hr class="styled">
                <div style="display:grid;grid-template-columns:auto 1fr;gap:0.4rem 1rem;font-size:0.83rem;">
                    <span style="color:var(--text-muted);">Waste Type</span>
                    <span style="font-weight:500;">{complaint.get('waste_type','—')}</span>
                    <span style="color:var(--text-muted);">AI Confidence</span>
                    <span style="font-weight:500;">{complaint.get('ai_confidence','—')}%  <span class="text-muted">(Demo · Phase 3 is real AI)</span></span>
                    <span style="color:var(--text-muted);">Assigned To</span>
                    <span style="font-weight:500;">{complaint.get('assigned_cleaner') or 'Not yet assigned'}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Resolved: before/after
        if complaint["status"] == "RESOLVED":
            st.markdown(
                f"""
                <div class="glass-card" style="background:var(--success-bg);border-color:rgba(45,106,79,0.25);">
                    <div style="display:flex;align-items:center;gap:0.5rem;margin-bottom:0.5rem;">
                        <span style="font-size:1.3rem;">🎉</span>
                        <div style="font-weight:700;color:#2d6a4f;font-family:'Outfit',sans-serif;">Cleanup Verified</div>
                    </div>
                    <div style="font-size:0.83rem;color:#5a5a7a;">
                        Resolved on: <strong>{complaint.get('resolved_at','—')}</strong><br>
                        Resolution time: <strong>{complaint.get('resolution_time','—')}</strong>
                    </div>
                    <hr class="styled">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;text-align:center;margin-top:0.5rem;">
                        <div>
                            <div style="font-size:0.7rem;color:#5a5a7a;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.3rem;">BEFORE</div>
                            <div style="background:rgba(198,40,40,0.08);border:1px dashed rgba(198,40,40,0.3);border-radius:8px;padding:2rem 0.5rem;color:var(--text-muted);font-size:0.75rem;">Before image<br>(Phase 3)</div>
                        </div>
                        <div>
                            <div style="font-size:0.7rem;color:#5a5a7a;font-weight:600;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:0.3rem;">AFTER</div>
                            <div style="background:rgba(45,106,79,0.08);border:1px dashed rgba(45,106,79,0.3);border-radius:8px;padding:2rem 0.5rem;color:var(--text-muted);font-size:0.75rem;">After image<br>(Phase 3)</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with right:
        # Status Timeline
        st.markdown('<div class="section-title">🕐 Status Timeline</div>', unsafe_allow_html=True)
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        render_timeline(complaint.get("timeline", []))
        st.markdown("</div>", unsafe_allow_html=True)

        # Map
        if complaint.get("lat"):
            render_map(
                [{"lat": complaint["lat"], "lon": complaint["lon"], "type": complaint["priority"], "label": complaint["location"]}],
                height=200,
                title="Location",
                show_legend=False,
            )


# ---------------------------------------------------------------------------
# Nearby Issues
# ---------------------------------------------------------------------------

def _render_nearby_issues() -> None:
    st.markdown(
        '<div class="page-title">📍 Nearby Waste Issues</div>'
        '<p class="page-subtitle">Waste complaints reported near your area.</p>',
        unsafe_allow_html=True,
    )

    markers = get_map_markers()
    render_map(markers, height=350, title="Waste Hotspot Map", show_legend=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Active Issues Near You</div>', unsafe_allow_html=True)

    all_complaints = get_complaints()
    active = [c for c in all_complaints if c["status"] != "RESOLVED"]
    for c in active:
        complaint_card(c, show_action=False)


# ---------------------------------------------------------------------------
# Awareness
# ---------------------------------------------------------------------------

def _render_awareness() -> None:
    st.markdown(
        '<div class="page-title">💡 Awareness</div>'
        '<p class="page-subtitle">Civic waste management tips and guidelines.</p>',
        unsafe_allow_html=True,
    )

    lang = st.radio(
        "Language",
        options=["English", "മലയാളം (Malayalam)"],
        horizontal=True,
        key="awareness_language",
        label_visibility="collapsed",
    )
    use_ml = "Malayalam" in lang

    content = get_awareness_content()

    # Featured
    featured = [c for c in content if c.get("featured")]
    if featured:
        st.markdown('<div class="section-title">⭐ Featured</div>', unsafe_allow_html=True)
        f_cols = st.columns(min(len(featured), 2))
        for col, item in zip(f_cols, featured):
            with col:
                title = item["title_ml"] if use_ml else item["title"]
                summary = item["summary_ml"] if use_ml else item["summary"]
                st.markdown(
                    f"""
                    <div class="awareness-card" style="border-left:4px solid {item['color']};">
                        <div style="font-size:1.5rem;margin-bottom:0.4rem;">{item['icon']}</div>
                        <div style="font-size:0.7rem;font-weight:600;color:{item['color']};text-transform:uppercase;letter-spacing:0.05em;margin-bottom:0.2rem;">{item['category']}</div>
                        <div style="font-weight:700;font-size:0.95rem;color:var(--text-primary);margin-bottom:0.4rem;">{title}</div>
                        <div style="font-size:0.82rem;color:#5a5a7a;line-height:1.5;">{summary}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # All content
    st.markdown('<div class="section-title">All Topics</div>', unsafe_allow_html=True)
    for item in content:
        title = item["title_ml"] if use_ml else item["title"]
        summary = item["summary_ml"] if use_ml else item["summary"]
        with st.expander(f"{item['icon']}  {title}"):
            st.markdown(f"**{item['category']}**")
            if use_ml:
                st.markdown(f"*{item['summary_ml']}*")
            else:
                st.markdown(f"*{item['summary']}*")
            for point in item["content"]:
                st.markdown(f"- {point}")

    st.markdown(
        '<div class="text-muted" style="margin-top:1rem;">Phase 3: RAG-powered personalized awareness content will be generated based on local waste patterns.</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

def _render_profile(user: dict) -> None:
    st.markdown(
        '<div class="page-title">👤 My Profile</div>'
        '<p class="page-subtitle">Your account details and settings.</p>',
        unsafe_allow_html=True,
    )

    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.markdown(
            f"""
            <div class="glass-card" style="text-align:center;padding:2rem;">
                <div class="avatar" style="width:60px;height:60px;font-size:1.3rem;margin:0 auto 1rem;">{user.get('avatar_initials','?')}</div>
                <div style="font-family:'Outfit',sans-serif;font-size:1.1rem;font-weight:700;">{user.get('name','—')}</div>
                <div style="font-size:0.82rem;color:var(--text-secondary);margin:0.2rem 0;">{user.get('email','—')}</div>
                <div class="sidebar-role-chip" style="margin-top:0.5rem;">Citizen</div>
                <div class="text-muted" style="margin-top:0.75rem;">Member since {user.get('joined','—')}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title" style="margin-top:0;">Account Details</div>
                <div style="display:grid;grid-template-columns:auto 1fr;gap:0.5rem 1.5rem;font-size:0.85rem;">
                    <span style="color:var(--text-muted);">Full Name</span><span style="font-weight:500;">{user.get('name','—')}</span>
                    <span style="color:var(--text-muted);">Email</span><span>{user.get('email','—')}</span>
                    <span style="color:var(--text-muted);">Phone</span><span>{user.get('phone','—')}</span>
                    <span style="color:var(--text-muted);">Ward</span><span>{user.get('ward','—')}</span>
                    <span style="color:var(--text-muted);">Total Reports</span><span style="font-weight:600;color:var(--brand);">{user.get('total_reports',0)}</span>
                    <span style="color:var(--text-muted);">Resolved</span><span style="font-weight:600;color:#2d6a4f;">{user.get('resolved',0)}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.button("✏️ Edit Profile (Phase 3)", disabled=True, use_container_width=True)
        st.button("🔑 Change Password (Phase 3)", disabled=True, use_container_width=True)
