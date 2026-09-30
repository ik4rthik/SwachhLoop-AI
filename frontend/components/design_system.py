"""
SwachhLoop AI — Design System
==============================
Glassmorphic design tokens and global CSS for Phase 2.

Usage:
    from frontend.components.design_system import inject_css
    inject_css()   # call once at the top of app.py

Color System:
    --brand-burgundy    #6B2737   Primary brand / actions
    --brand-burgundy-lt #8B3A4E   Lighter variant
    --glass-bg          rgba(255,255,255,0.72)
    --glass-border      rgba(255,255,255,0.85)
    --text-primary      #1a1a2e
    --text-secondary    #5a5a7a
    --success           #2d6a4f
    --status-critical   #c62828
    --status-high       #e65100
    --status-medium     #f57f17
    --status-low        #2d6a4f
"""

import streamlit as st


DESIGN_SYSTEM_CSS = """
<style>

/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700&display=swap');

/* ── CSS Custom Properties ── */
:root {
  --brand:           #6B2737;
  --brand-light:     #8B3A4E;
  --brand-dark:      #4a1825;
  --brand-alpha:     rgba(107, 39, 55, 0.08);
  --brand-alpha-md:  rgba(107, 39, 55, 0.15);

  --success:         #2d6a4f;
  --success-bg:      rgba(45, 106, 79, 0.10);
  --success-light:   #40916c;

  --status-critical: #c62828;
  --status-high:     #e65100;
  --status-medium:   #f57f17;
  --status-low:      #2d6a4f;

  --bg-page:         #f4f1f0;
  --bg-sidebar:      rgba(255,255,255,0.82);
  --glass-surface:   rgba(255,255,255,0.72);
  --glass-border:    rgba(255,255,255,0.85);
  --glass-shadow:    0 4px 24px rgba(107,39,55,0.07), 0 1px 6px rgba(0,0,0,0.04);
  --glass-shadow-lg: 0 8px 40px rgba(107,39,55,0.10), 0 2px 12px rgba(0,0,0,0.06);
  --glass-blur:      blur(16px);

  --text-primary:    #1a1a2e;
  --text-secondary:  #5a5a7a;
  --text-muted:      #9090a8;
  --text-inverse:    #ffffff;

  --radius-sm:   8px;
  --radius-md:   14px;
  --radius-lg:   20px;
  --radius-xl:   28px;
  --radius-full: 9999px;

  --transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Global Reset / Base ── */
*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: var(--bg-page) !important;
  color: var(--text-primary);
}

/* ── Streamlit skeleton overrides ── */
[data-testid="stAppViewContainer"] > .main { background: transparent; }
[data-testid="stHeader"] { background: transparent !important; }
footer { visibility: hidden !important; }
#MainMenu { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── Sidebar ── */
[data-testid="stSidebar"] {
  background: var(--bg-sidebar) !important;
  backdrop-filter: var(--glass-blur) !important;
  -webkit-backdrop-filter: var(--glass-blur) !important;
  border-right: 1px solid rgba(255,255,255,0.6) !important;
  box-shadow: 4px 0 24px rgba(107,39,55,0.06) !important;
}

/* ── Main content area ── */
.block-container {
  padding: 1.5rem 2rem 2rem !important;
  max-width: 1400px !important;
}

/* ── Glass Card ── */
.glass-card {
  background: var(--glass-surface);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
  padding: 1.5rem;
  margin-bottom: 1rem;
  transition: var(--transition);
}
.glass-card:hover {
  box-shadow: var(--glass-shadow-lg);
  transform: translateY(-1px);
}

/* ── Stat Card ── */
.stat-card {
  background: var(--glass-surface);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  box-shadow: var(--glass-shadow);
  padding: 1.25rem 1.5rem;
  transition: var(--transition);
}
.stat-card:hover { box-shadow: var(--glass-shadow-lg); transform: translateY(-1px); }
.stat-card .stat-value { font-family: 'Outfit', sans-serif; font-size: 2rem; font-weight: 700; color: var(--text-primary); line-height: 1.1; }
.stat-card .stat-label { font-size: 0.8rem; font-weight: 500; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 0.06em; margin-top: 0.25rem; }
.stat-card .stat-icon { font-size: 1.5rem; margin-bottom: 0.5rem; }
.stat-card.brand .stat-value { color: var(--brand); }
.stat-card.success .stat-value { color: var(--success); }
.stat-card.critical .stat-value { color: var(--status-critical); }
.stat-card.warning .stat-value { color: var(--status-high); }

/* ── Status Badges ── */
.badge {
  display: inline-flex; align-items: center;
  padding: 0.2em 0.75em;
  border-radius: var(--radius-full);
  font-size: 0.75rem; font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.badge-submitted  { background: rgba(90,90,122,0.10); color: var(--text-secondary); }
.badge-validated  { background: rgba(21,101,192,0.10); color: #1565c0; }
.badge-assigned   { background: rgba(230,81,0,0.10); color: #bf360c; }
.badge-cleaning   { background: rgba(245,127,23,0.12); color: #e65100; }
.badge-verification { background: rgba(107,39,55,0.10); color: var(--brand); }
.badge-resolved   { background: var(--success-bg); color: var(--success); }
.badge-escalated  { background: rgba(198,40,40,0.10); color: var(--status-critical); }
.badge-pending    { background: rgba(245,127,23,0.10); color: #e65100; }
.badge-in-progress { background: rgba(107,39,55,0.10); color: var(--brand); }
.badge-completed  { background: var(--success-bg); color: var(--success); }

.priority-critical { background: rgba(198,40,40,0.12); color: var(--status-critical); }
.priority-high     { background: rgba(230,81,0,0.12); color: var(--status-high); }
.priority-medium   { background: rgba(245,127,23,0.12); color: var(--status-medium); }
.priority-low      { background: var(--success-bg); color: var(--success-light); }

/* ── Buttons ── */
.btn-primary {
  background: var(--brand);
  color: #fff;
  border: none;
  border-radius: var(--radius-md);
  padding: 0.65rem 1.5rem;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
  display: inline-flex; align-items: center; gap: 0.5rem;
  text-decoration: none;
}
.btn-primary:hover { background: var(--brand-light); transform: translateY(-1px); box-shadow: 0 4px 16px rgba(107,39,55,0.25); }

.btn-secondary {
  background: var(--glass-surface);
  color: var(--brand);
  border: 1.5px solid var(--brand);
  border-radius: var(--radius-md);
  padding: 0.6rem 1.4rem;
  font-family: 'Inter', sans-serif;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: var(--transition);
  display: inline-flex; align-items: center; gap: 0.5rem;
}
.btn-secondary:hover { background: var(--brand-alpha); }

/* ── Streamlit button override ── */
.stButton > button {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  border-radius: var(--radius-md) !important;
  transition: var(--transition) !important;
}
.stButton > button[kind="primary"] {
  background: var(--brand) !important;
  border-color: var(--brand) !important;
}
.stButton > button[kind="primary"]:hover {
  background: var(--brand-light) !important;
  border-color: var(--brand-light) !important;
  box-shadow: 0 4px 16px rgba(107,39,55,0.25) !important;
}

/* ── Page title typography ── */
.page-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 0.25rem;
  line-height: 1.2;
}
.page-subtitle { font-size: 0.9rem; color: var(--text-secondary); margin: 0; }
.section-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 1.5rem 0 0.75rem;
}

/* ── Top bar ── */
.topbar {
  background: var(--glass-surface);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
  padding: 0.75rem 1.5rem;
  margin-bottom: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.topbar-brand { font-family: 'Outfit', sans-serif; font-size: 1.2rem; font-weight: 700; color: var(--brand); }
.topbar-user { font-size: 0.85rem; color: var(--text-secondary); font-weight: 500; }

/* ── Sidebar nav ── */
.sidebar-logo {
  font-family: 'Outfit', sans-serif;
  font-size: 1.3rem;
  font-weight: 700;
  color: var(--brand);
  padding: 0.5rem 0;
}
.sidebar-role-chip {
  background: var(--brand-alpha);
  color: var(--brand);
  border-radius: var(--radius-full);
  padding: 0.2em 0.7em;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  display: inline-block;
  margin-bottom: 1rem;
}
.nav-item {
  display: flex; align-items: center; gap: 0.6rem;
  padding: 0.6rem 0.85rem;
  border-radius: var(--radius-md);
  font-size: 0.88rem; font-weight: 500;
  color: var(--text-secondary);
  cursor: pointer;
  transition: var(--transition);
  margin: 0.1rem 0;
  text-decoration: none;
  border: none; background: transparent; width: 100%; text-align: left;
}
.nav-item:hover { background: var(--brand-alpha); color: var(--brand); }
.nav-item.active { background: var(--brand-alpha-md); color: var(--brand); font-weight: 600; }
.nav-separator { height: 1px; background: rgba(107,39,55,0.08); margin: 0.75rem 0; }

/* ── Complaint / Task Card ── */
.complaint-card {
  background: var(--glass-surface);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  box-shadow: var(--glass-shadow);
  padding: 1rem 1.25rem;
  margin-bottom: 0.75rem;
  transition: var(--transition);
}
.complaint-card:hover { box-shadow: var(--glass-shadow-lg); transform: translateY(-1px); border-color: var(--brand-alpha); }
.complaint-card-title { font-weight: 600; font-size: 0.95rem; color: var(--text-primary); margin: 0 0 0.25rem; }
.complaint-card-meta { font-size: 0.78rem; color: var(--text-secondary); }
.complaint-card-id { font-size: 0.72rem; color: var(--text-muted); font-family: monospace; }

/* ── Timeline ── */
.timeline { padding: 0.5rem 0; }
.timeline-step { display: flex; gap: 1rem; margin-bottom: 0.5rem; }
.timeline-indicator { display: flex; flex-direction: column; align-items: center; }
.timeline-dot {
  width: 14px; height: 14px;
  border-radius: 50%;
  border: 2px solid #ccc;
  background: #fff;
  flex-shrink: 0;
  transition: var(--transition);
}
.timeline-dot.done { background: var(--success); border-color: var(--success); }
.timeline-dot.active { background: var(--brand); border-color: var(--brand); box-shadow: 0 0 0 4px var(--brand-alpha); }
.timeline-line { width: 2px; flex: 1; background: #e0e0e0; margin: 2px 0; min-height: 20px; }
.timeline-line.done { background: var(--success); }
.timeline-content { padding-bottom: 0.5rem; flex: 1; }
.timeline-label { font-size: 0.85rem; font-weight: 600; color: var(--text-primary); }
.timeline-label.done { color: var(--success); }
.timeline-label.pending { color: var(--text-muted); }
.timeline-time { font-size: 0.72rem; color: var(--text-muted); }

/* ── Map card ── */
.map-card {
  background: linear-gradient(135deg, #e8f4f8 0%, #dce8f0 100%);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
  overflow: hidden;
  position: relative;
}
.map-placeholder {
  display: flex; align-items: center; justify-content: center;
  flex-direction: column;
  min-height: 260px;
  color: var(--text-muted);
}

/* ── Alert / notification styles ── */
.notif-card {
  display: flex; gap: 0.75rem; align-items: flex-start;
  background: var(--glass-surface);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-md);
  padding: 0.85rem 1rem;
  margin-bottom: 0.5rem;
  transition: var(--transition);
}
.notif-card:hover { box-shadow: var(--glass-shadow); }
.notif-card.unread { border-left: 3px solid var(--brand); }
.notif-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 0.25rem; flex-shrink: 0; }
.notif-dot.success { background: var(--success); }
.notif-dot.info { background: #1565c0; }
.notif-dot.warning { background: var(--status-medium); }
.notif-dot.error { background: var(--status-critical); }

/* ── Form styles ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
  border-radius: var(--radius-md) !important;
  border: 1px solid rgba(107,39,55,0.15) !important;
  font-family: 'Inter', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--brand) !important;
  box-shadow: 0 0 0 3px var(--brand-alpha) !important;
}

/* ── Success state ── */
.success-banner {
  background: linear-gradient(135deg, var(--success-bg) 0%, rgba(64,145,108,0.08) 100%);
  border: 1.5px solid var(--success-light);
  border-radius: var(--radius-lg);
  padding: 2rem;
  text-align: center;
}
.success-banner .success-icon { font-size: 3rem; margin-bottom: 0.5rem; }
.success-banner .success-title { font-family: 'Outfit', sans-serif; font-size: 1.5rem; font-weight: 700; color: var(--success); }

/* ── AI badge ── */
.ai-badge {
  background: linear-gradient(135deg, var(--brand-alpha) 0%, rgba(107,39,55,0.05) 100%);
  border: 1px solid var(--brand-alpha-md);
  border-radius: var(--radius-md);
  padding: 0.75rem 1rem;
}
.ai-badge-label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.08em; color: var(--brand); }
.ai-badge-value { font-size: 1rem; font-weight: 600; color: var(--text-primary); }

/* ── Landing page specific ── */
.hero-section {
  text-align: center;
  padding: 3rem 2rem;
}
.hero-title {
  font-family: 'Outfit', sans-serif;
  font-size: 3rem; font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
  margin-bottom: 1rem;
}
.hero-title span { color: var(--brand); }
.hero-subtitle { font-size: 1.1rem; color: var(--text-secondary); max-width: 560px; margin: 0 auto 2rem; line-height: 1.6; }

.loop-step {
  display: inline-flex; align-items: center; gap: 0.5rem;
  background: var(--glass-surface);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-full);
  padding: 0.4rem 1rem;
  font-size: 0.85rem; font-weight: 600;
  color: var(--text-primary);
  box-shadow: var(--glass-shadow);
}
.loop-arrow { color: var(--brand); font-weight: 700; }

.feature-card {
  background: var(--glass-surface);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
  padding: 1.5rem;
  text-align: center;
  transition: var(--transition);
  height: 100%;
}
.feature-card:hover { box-shadow: var(--glass-shadow-lg); transform: translateY(-2px); }
.feature-card .feature-icon { font-size: 2.2rem; margin-bottom: 0.75rem; }
.feature-card .feature-title { font-family: 'Outfit', sans-serif; font-size: 1rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.4rem; }
.feature-card .feature-desc { font-size: 0.82rem; color: var(--text-secondary); line-height: 1.5; }

/* ── Login page ── */
.login-card {
  background: var(--glass-surface);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  box-shadow: var(--glass-shadow-lg);
  padding: 2.5rem;
}

/* ── Divider ── */
hr.styled { border: none; height: 1px; background: rgba(107,39,55,0.08); margin: 1.25rem 0; }

/* ── Awareness cards ── */
.awareness-card {
  background: var(--glass-surface);
  backdrop-filter: var(--glass-blur);
  -webkit-backdrop-filter: var(--glass-blur);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-lg);
  box-shadow: var(--glass-shadow);
  padding: 1.25rem;
  transition: var(--transition);
  height: 100%;
}
.awareness-card:hover { box-shadow: var(--glass-shadow-lg); transform: translateY(-1px); }

/* ── Avatar ── */
.avatar {
  width: 38px; height: 38px;
  border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  font-family: 'Outfit', sans-serif;
  font-weight: 700; font-size: 0.85rem;
  color: #fff;
  background: var(--brand);
  flex-shrink: 0;
}

/* ── Metric overrides ── */
[data-testid="stMetric"] {
  background: var(--glass-surface) !important;
  border: 1px solid var(--glass-border) !important;
  border-radius: var(--radius-md) !important;
  padding: 1rem !important;
  box-shadow: var(--glass-shadow) !important;
}

/* ── Tab styling ── */
.stTabs [data-baseweb="tab-list"] {
  gap: 0.5rem;
  background: transparent !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: var(--radius-md) !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
  background: var(--brand-alpha-md) !important;
  color: var(--brand) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(107,39,55,0.2); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(107,39,55,0.35); }

/* ── Misc utility ── */
.text-muted { color: var(--text-muted) !important; font-size: 0.8rem; }
.text-secondary-color { color: var(--text-secondary); }
.brand-color { color: var(--brand); }
.fw-600 { font-weight: 600; }
.mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 0.85em; }

</style>
"""


def inject_css() -> None:
    """Inject the global SwachhLoop AI design system CSS into the Streamlit page."""
    st.markdown(DESIGN_SYSTEM_CSS, unsafe_allow_html=True)
