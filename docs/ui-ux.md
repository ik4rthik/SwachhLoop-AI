# SwachhLoop AI — UI/UX Design System

> **Phase:** 2 — Unified Frontend Prototype  
> **Last updated:** September 2026

---

## Overview

SwachhLoop AI uses a **glassmorphic design system** built on top of Streamlit. The entire frontend is one application with role-based views, controlled by session state.

---

## Color System

| Token | Hex | Usage |
|-------|-----|-------|
| `--brand` | `#6B2737` | Primary brand · Burgundy wine red |
| `--brand-light` | `#8B3A4E` | Hover states · Lighter brand |
| `--brand-dark` | `#4a1825` | Deep brand for emphasis |
| `--brand-alpha` | `rgba(107,39,55,0.08)` | Glass card background tint |
| `--success` | `#2d6a4f` | Resolved / environmental states |
| `--success-light` | `#40916c` | Lighter success accents |
| `--bg-page` | `#f4f1f0` | Overall page background |
| `--glass-surface` | `rgba(255,255,255,0.72)` | Card / sidebar glass surface |
| `--glass-border` | `rgba(255,255,255,0.85)` | Card borders |
| `--text-primary` | `#1a1a2e` | Main text |
| `--text-secondary` | `#5a5a7a` | Body / secondary text |
| `--text-muted` | `#9090a8` | Captions, hints |

### Status Colors

| Priority / Status | Color | Usage |
|-------------------|-------|-------|
| CRITICAL | `#c62828` | Immediate action required |
| HIGH | `#e65100` | Urgent |
| MEDIUM | `#f57f17` | Normal priority |
| LOW / RESOLVED | `#2d6a4f` | Green — completed / safe |

---

## Typography

| Role | Font | Weight | Size |
|------|------|--------|------|
| Page titles | Outfit | 700 | 1.8rem |
| Section titles | Outfit | 600 | 1.1rem |
| KPI values | Outfit | 700 | 2rem |
| Body | Inter | 400 | 0.88rem |
| Labels | Inter | 500–600 | 0.78–0.85rem |
| Captions | Inter | 400 | 0.72rem |
| Code / IDs | Monospace | 400 | 0.82em |

---

## Glass Effect System

All glass surfaces use:
```css
background: rgba(255, 255, 255, 0.72);
backdrop-filter: blur(16px);
border: 1px solid rgba(255, 255, 255, 0.85);
border-radius: 20px;
box-shadow: 0 4px 24px rgba(107,39,55,0.07), 0 1px 6px rgba(0,0,0,0.04);
```

Hover state:
```css
box-shadow: 0 8px 40px rgba(107,39,55,0.10), 0 2px 12px rgba(0,0,0,0.06);
transform: translateY(-1px);
```

---

## Component System

All components are in `frontend/components/`.

### `design_system.py`
- `inject_css()` — injects all global CSS tokens, component styles, and utility classes.

### `layout.py`
- `render_sidebar(role, user)` — role-aware sidebar. Returns current page key.
- `render_topbar(user, role, page_title)` — glass top navigation bar with brand + user info.

### `cards.py`
- `stat_card(label, value, icon, variant, delta)` — KPI metric glass card. Variants: `default`, `brand`, `success`, `critical`, `warning`.
- `complaint_card(complaint, show_action, action_label)` — complaint list item. Returns True if action clicked.
- `task_card(task)` — cleaner task card with priority color border. Returns True if view button clicked.
- `ai_assessment_card(waste_type, confidence, priority, reason)` — AI analysis result block.

### `badges.py`
- `status_badge_html(status)` → HTML string
- `priority_badge_html(priority)` → HTML string
- `render_status_badge(status)` — renders via `st.markdown`
- `render_priority_badge(priority)` — renders via `st.markdown`
- `render_badge_row(status, priority)` — both side by side

### `timeline.py`
- `render_timeline(steps)` — vertical status timeline.
  - `steps`: list of `{step, done, time}` dicts.

### `map_widget.py`
- `render_map(markers, height, title, show_legend)` — prototype SVG map with markers.
  - `markers`: list of `{lat, lon, type, label}` dicts.
  - Phase 3/4: replace internals with Folium/Leaflet.

### `notifications_widget.py`
- `render_notifications(notifications, role)` — renders unread + read notification cards.

---

## Role-Based Navigation

Navigation is implemented via `st.session_state["current_page"]` and Streamlit buttons. No router library needed.

| Role | Nav Items |
|------|-----------|
| Citizen | Dashboard, Report Waste, My Complaints, Nearby Issues, Awareness, Notifications, Profile |
| Cleaner | Dashboard, My Tasks, Map, Task History, Notifications, Profile |
| Municipal Staff | Dashboard, Complaints, Waste Map, Tasks, Escalations, Analytics, Notifications, Profile |
| Admin | Dashboard, Users, AI Monitoring, Knowledge Base, Audit Logs, Settings |

---

## Page Structure

```
app.py
├── Landing (public — no sidebar)
├── Login (public — no sidebar)
└── App (authenticated)
    ├── Sidebar (role-aware)
    ├── Top Bar (glass)
    └── Pages (per role)
        ├── citizen.py
        │   ├── dashboard
        │   ├── report_waste
        │   ├── my_complaints
        │   ├── [complaint_detail] (via session state)
        │   ├── nearby_issues
        │   ├── awareness
        │   ├── notifications
        │   └── profile
        ├── cleaner.py
        │   ├── dashboard
        │   ├── my_tasks
        │   ├── [task_detail] (via session state)
        │   ├── map
        │   ├── task_history
        │   ├── notifications
        │   └── profile
        ├── municipal_staff.py
        │   ├── dashboard
        │   ├── complaints
        │   ├── [complaint_detail] (via session state)
        │   ├── waste_map
        │   ├── tasks
        │   ├── escalations
        │   ├── analytics
        │   ├── notifications
        │   └── profile
        └── admin.py
            ├── dashboard
            ├── users
            ├── ai_monitoring
            ├── knowledge_base
            ├── audit_logs
            └── settings
```

---

## Mock Data Strategy

All prototype data lives in `frontend/data/mock_data.py`.

| Data | Description |
|------|-------------|
| `DEMO_USERS` | 4 demo accounts (Citizen, Cleaner, Staff, Admin) |
| `MOCK_COMPLAINTS` | 5 realistic complaints with full timeline data |
| `MOCK_TASKS` | 4 tasks for the Cleaner demo |
| `MOCK_NOTIFICATIONS` | Per-role notification lists |
| `MOCK_MAP_MARKERS` | Lat/lon markers for the prototype map |
| `MOCK_AWARENESS_CONTENT` | 5 awareness articles (English + Malayalam) |
| `MOCK_USERS_ADMIN` | 8 users for admin user management |
| `MOCK_SYSTEM_HEALTH` | Service health indicators |
| `MUNICIPAL_STATS` | KPI numbers for the municipal dashboard |
| `MOCK_AUDIT_LOG` | 8 audit log entries |

---

## Future API Integration Boundaries

All data access goes through `frontend/services/api_client.py`.

**To connect Phase 3 real API**, replace each function body:

```python
# Phase 2 (current):
def get_complaints(citizen_id=None):
    return [c for c in MOCK_COMPLAINTS if ...]

# Phase 3 replacement:
def get_complaints(citizen_id=None):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{API_BASE_URL}/complaints", params={"citizen_id": citizen_id})
        return resp.json()
```

Page components import from `api_client` only — they never touch mock data directly.

### API Endpoint Mapping

| Function | Phase 3 Backend Endpoint |
|----------|--------------------------|
| `authenticate_user()` | `POST /auth/login` |
| `get_complaints()` | `GET /complaints` |
| `get_complaint_by_id()` | `GET /complaints/{id}` |
| `submit_complaint()` | `POST /complaints` |
| `get_tasks()` | `GET /tasks` |
| `update_task_status()` | `PATCH /tasks/{id}` |
| `get_notifications()` | `GET /notifications` |
| `get_map_markers()` | `GET /complaints/map-markers` |
| `get_awareness_content()` | `GET /awareness` |
| `get_all_users()` | `GET /admin/users` |
| `get_system_health()` | `GET /admin/health` |
| `get_audit_log()` | `GET /admin/audit-log` |
| `check_backend_health()` | `GET /health` (real — already implemented) |

---

## Map Integration Path

Phase 2 uses an SVG placeholder map (`map_widget.py`).

Phase 3/4 upgrade:
```python
# Replace render_map() body with:
import folium
from streamlit_folium import st_folium

m = folium.Map(location=[10.527, 76.214], zoom_start=13)
for marker in markers:
    color = MARKER_COLORS.get(marker["type"], "gray")
    folium.CircleMarker(
        location=[marker["lat"], marker["lon"]],
        radius=12,
        color=color,
        fill=True,
        popup=marker["label"],
    ).add_to(m)
st_folium(m, height=height)
```

Add to `requirements.txt`: `folium`, `streamlit-folium`.

---

## Running the Application

```bash
# Terminal 1 — Backend (Phase 1 endpoints)
uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Frontend
streamlit run frontend/app.py
```

**Demo Accounts:**

| Role | Email | Password |
|------|-------|----------|
| Citizen | citizen@swachhloop.ai | demo123 |
| Cleaner | cleaner@swachhloop.ai | demo123 |
| Municipal Staff | staff@swachhloop.ai | demo123 |
| Admin | admin@swachhloop.ai | demo123 |
