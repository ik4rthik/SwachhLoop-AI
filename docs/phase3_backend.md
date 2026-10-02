# SwachhLoop AI — Phase 3 Backend Documentation

> Phase 3: Authentication + Database + Backend Integration  
> Branch: `phase-3-backend`

---

## Overview

Phase 3 connects the Phase 2 Streamlit prototype to a real FastAPI backend with:
- **JWT-based authentication** (bcrypt passwords, HS256 tokens)
- **SQLite database** for local dev (SQLAlchemy async ORM)
- **5 real API route groups** replacing all mock data in the frontend
- **Role-based authorization** enforced server-side
- **Audit logging** for all significant actions
- **Image upload abstraction** (local → S3-ready)

---

## Quick Start

```bash
# 1. Activate venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env (copy from .env.example)
copy .env.example .env

# 4. Start backend (creates SQLite DB + seeds demo users on first run)
uvicorn backend.main:app --reload --port 8000

# 5. Start frontend (separate terminal)
streamlit run frontend/app.py

# 6. Run tests
pytest tests/ -v
```

### Demo credentials
All demo accounts use password: `demo123`

| Role | Email |
|------|-------|
| Citizen | citizen@swachhloop.ai |
| Cleaner | cleaner@swachhloop.ai |
| Municipal Staff | staff@swachhloop.ai |
| Admin | admin@swachhloop.ai |

---

## Database Schema

### `users`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | Auto-increment |
| email | VARCHAR(255) UNIQUE | Lowercased on insert |
| hashed_password | VARCHAR(255) | bcrypt hash |
| full_name | VARCHAR(255) | |
| role | ENUM | citizen \| cleaner \| municipal_staff \| admin |
| phone | VARCHAR(20) | Optional |
| ward | VARCHAR(100) | Optional |
| employee_id | VARCHAR(50) | Cleaner/Staff/Admin |
| department | VARCHAR(100) | Staff/Admin |
| avatar_initials | VARCHAR(10) | Auto-generated from name |
| is_active | BOOLEAN | Default true |
| created_at | DATETIME | |
| updated_at | DATETIME | |

### `complaints`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| citizen_id | FK → users.id | CASCADE delete |
| image_url | VARCHAR(500) | Optional |
| latitude / longitude | FLOAT | Optional |
| location_label | VARCHAR(300) | |
| reported_at | DATETIME | |
| updated_at | DATETIME | |
| status | ENUM | SUBMITTED→VALIDATED→ASSIGNED→CLEANING→VERIFICATION→RESOLVED→ESCALATED |
| priority | ENUM | LOW \| MEDIUM \| HIGH \| CRITICAL |
| waste_type | VARCHAR(100) | Optional (AI fills in Phase 4) |
| waste_confidence | FLOAT | 0.0–1.0 (AI placeholder) |
| title / description | VARCHAR/TEXT | |

### `cleaning_tasks`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| complaint_id | FK → complaints.id | |
| assigned_to | FK → users.id | Cleaner (nullable) |
| assigned_by | FK → users.id | Staff (nullable) |
| status | ENUM | PENDING \| IN_PROGRESS \| COMPLETED \| CANCELLED |
| before/after_image_url | VARCHAR(500) | |
| assigned_at / completed_at | DATETIME | |

### `notifications`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| user_id | FK → users.id | |
| type | ENUM | info \| success \| warning \| error |
| title / message | VARCHAR/TEXT | |
| is_read | BOOLEAN | Default false |
| created_at | DATETIME | |

### `audit_logs`
| Column | Type | Notes |
|--------|------|-------|
| id | INTEGER PK | |
| actor_id | FK → users.id | Nullable (system actions) |
| action | VARCHAR(100) | LOGIN, SUBMIT_COMPLAINT, etc. |
| resource_type / resource_id | VARCHAR | complaint, task, user |
| detail | TEXT | Human-readable description |
| ip_address | VARCHAR(50) | |
| created_at | DATETIME | |

---

## API Endpoints

### Authentication (`/api/auth/`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/register` | None | Create new citizen account (privileged role registration strictly blocked with 403) |
| POST | `/login` | None | Get JWT token (verifies active account, bcrypt hash) |
| GET | `/me` | JWT | Current user profile |

**Login response:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": 1, "email": "...", "role": "citizen", ... }
}
```

### Complaints (`/api/complaints/`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `` | Citizen | Submit complaint (multipart/form-data) |
| GET | `` | All | List (citizen=own, cleaner=assigned only, staff/admin=all) |
| GET | `/map-markers` | All | Map coordinates |
| GET | `/{id}` | All | Single complaint (ownership/assignment enforced) |
| PATCH | `/{id}/status` | Staff/Admin | Update status (query or JSON body) |
| PATCH | `/{id}/assign` | Staff/Admin | Assign to cleaner (creates cleaning task & moves to ASSIGNED) |

### Tasks (`/api/tasks/`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `` | Staff/Admin/Cleaner | List tasks (cleaner=own only, staff/admin=all, citizen=403 Forbidden) |
| GET | `/cleaners` | Staff/Admin | List active cleaners available for assignment |
| GET | `/{id}` | Staff/Admin/Cleaner | Single task (cleaner=own only) |
| PATCH | `/{id}` | Staff/Admin/Cleaner | Update status (syncs complaint to CLEANING or VERIFICATION) |
| POST | `/{id}/evidence` | Staff/Admin/Cleaner | Upload after-image proof |

### Notifications (`/api/notifications/`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `` | JWT | User's notifications |
| PATCH | `/{id}/read` | JWT | Mark as read |

### Admin (`/api/admin/`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/users` | Admin | All users |
| POST | `/users` | Admin | Create privileged user (cleaner, municipal_staff, admin, citizen) |
| PATCH | `/users/{id}?is_active=` | Admin | Toggle active status (cannot deactivate own account) |
| GET | `/audit-log` | Admin | Audit log |
| GET | `/health` | Admin | System health and database connectivity |

### Stats (`/api/stats/`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/municipal` | Staff/Admin | Dashboard stats |

### Health (`/`)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | None | Backend health check |
| GET | `/status` | None | Backend status |

---

## Authentication Architecture

```
POST /api/auth/login
  → verify email + bcrypt hash
  → create JWT: {sub: user_id, role: user.role, exp: +60min}
  → write AuditLog: action=LOGIN
  → return {access_token, user}

FastAPI dependency: get_current_user()
  → extract Bearer token from Authorization header
  → decode JWT (python-jose)
  → fetch User from DB by ID
  → verify is_active
  → return User ORM object

Role guards:
  require_citizen, require_cleaner, require_staff,
  require_admin, require_staff_or_admin
```

JWT payload:
```json
{"sub": "1", "role": "citizen", "exp": 1740000000}
```

---

## Frontend Integration

The `frontend/services/api_client.py` has been fully updated:
- All functions call the real backend with `httpx` (synchronous, Streamlit-compatible)
- JWT token stored in `st.session_state["access_token"]`
- All calls include `Authorization: Bearer {token}` header
- 401 responses clear session and redirect to login
- If backend is unreachable, falls back to mock data gracefully
- API responses normalized to Phase 2 data format (no page changes needed)

---

## Running Tests

```bash
# Run all Phase 3 tests (56 tests)
pytest tests/ -v

# Run specific test files
pytest tests/test_auth.py -v
pytest tests/test_complaints.py -v
pytest tests/test_tasks.py -v
pytest tests/test_admin.py -v
pytest tests/test_audit.py -v
pytest tests/test_persistence.py -v
```

Tests run against an isolated SQLite test database with automatic rollback/isolation — no running backend or PostgreSQL needed.

---

## Moving to Production (PostgreSQL/Supabase)

1. Change `DATABASE_URL` in `.env`:
   ```
   DATABASE_URL=postgresql+asyncpg://user:password@host:5432/dbname
   ```

2. Install `asyncpg` (requires C compiler or pre-built wheel):
   ```bash
   pip install asyncpg
   ```

3. Run the app — SQLAlchemy will create tables on startup via `init_db()`.

4. For production, replace `create_all()` with **Alembic migrations** (Phase 4+).

---

## Known Limitations (Phase 3)

- **No Alembic migrations** — schema changes require manual `drop_all()` + `create_all()` in dev
- **Awareness content is static** — RAG pipeline planned for Phase 4
- **No token refresh** — expired tokens require re-login
- **No email verification** — registration is open (restrict in production)
- **Local image storage only** — S3 backend interface defined but not implemented
- **AI fields are placeholders** — `waste_confidence`, AI service stubs untouched
- **No WebSocket notifications** — real-time updates planned for Phase 4+
- **Password reset not implemented** — button shown but disabled in UI
