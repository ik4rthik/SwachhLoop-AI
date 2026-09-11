# ♻️ SwachhLoop AI

**An Autonomous Multi-Agent System for Closed-Loop Smart Civic Waste Management**

> Final-Year B.Tech AI Project  
> 🚧 **Active development**

SwachhLoop AI is a civic waste-management platform designed to close the loop from waste reporting to verified resolution.

---

## Core Workflow

**Report → Validate → Classify → Prioritize → Locate → Optimize → Collect → Verify → Resolve / Escalate**

---

## Table of Contents

- [Project Overview](#project-overview)
- [Roles](#roles)
- [Architecture](#architecture)
- [AI Components](#ai-components)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Configuration](#environment-configuration)
  - [Running the Backend](#running-the-backend)
  - [Running the Frontend](#running-the-frontend)
- [Development Workflow](#development-workflow)
- [Development Phases](#development-phases)
- [Project Principle](#project-principle)
- [Repository Workflow](#repository-workflow)

---

## Project Overview

SwachhLoop AI digitizes the civic waste management lifecycle:

1. **Citizens** report waste via a web interface (optionally with photos).
2. **AI agents** classify waste type, assess urgency, and route cleanup tasks.
3. **Cleaners** receive optimized task assignments and submit completion proof.
4. **Municipal Staff** oversee the pipeline and escalate issues.
5. **AI** verifies cleanup completion via before/after image comparison.

The system is designed as a closed-loop: a complaint raised by a citizen is automatically tracked until verified resolution.

---

## Roles

- **Citizen** — report waste, track complaints, view nearby issues and awareness content.
- **Cleaner** — receive assigned cleaning tasks, navigate to locations, submit after-cleanup evidence.
- **Municipal Staff** — manage complaints, priorities, tasks, maps, routes, escalations and analytics.
- **Admin** — manage users, knowledge base, AI monitoring, audit logs and system settings.

---

## Architecture

```text
One Website
    ↓
Authentication / Role Detection
    ├── Citizen Dashboard
    ├── Cleaner Dashboard
    ├── Municipal Dashboard
    └── Admin Dashboard
            ↓
       FastAPI Backend
            ↓
        Service Layer
            ↓
       Database / Storage
            ↓
        AI / Agent Layer
```

See [`docs/architecture.md`](docs/architecture.md) for the full architecture diagram.

---

## AI Components

> Phase 3+ — interfaces are defined in `backend/services/`, implementations come later.

- Open-source YOLO-family computer vision for waste detection/classification
- LangGraph multi-agent orchestration
- Self-Corrective RAG for knowledge-intensive decisions and awareness generation
- OpenStreetMap with NetworkX / OR-Tools for deterministic route optimization
- Image change detection for cleanup verification
- Cross-cutting guardrails and evaluation

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit |
| Backend API | FastAPI + Uvicorn |
| Data validation | Pydantic v2 |
| Configuration | pydantic-settings + python-dotenv |
| Database | PostgreSQL + SQLAlchemy (async) |
| AI (Phase 3+) | LangGraph, YOLO, Gemini/OpenAI, ChromaDB |
| Route optimization (Phase 4+) | NetworkX / OR-Tools, OpenStreetMap, Folium |
| Development | Python 3.11+, ruff, pytest |

---

## Project Structure

```
SwachhLoop-AI/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── core/config.py           # All settings (reads from .env)
│   ├── api/
│   │   ├── routes/health.py     # /health and /status endpoints
│   │   └── dependencies.py      # Shared dependencies (auth, db)
│   ├── models/schemas.py        # Shared Pydantic schemas
│   ├── services/                # AI service interfaces (ABCs — Phase 3/4)
│   │   ├── waste_detector.py
│   │   ├── complaint_analyzer.py
│   │   ├── route_optimizer.py
│   │   └── cleanup_verifier.py
│   └── db/session.py            # Async DB session factory
│
├── frontend/
│   ├── app.py                   # Streamlit entry point + role selector
│   ├── components/              # Shared UI components (Phase 2+)
│   └── pages/
│       ├── citizen.py
│       ├── cleaner.py
│       ├── municipal_staff.py
│       └── admin.py
│
├── docs/architecture.md         # Full architecture diagram + design principles
├── .env.example                 # Environment variable template (copy to .env)
├── requirements.txt             # Runtime dependencies
├── requirements-dev.txt         # Development/test dependencies
└── README.md
```

---

## Getting Started

### Prerequisites

- Python **3.11+**
- pip
- (Phase 2+) PostgreSQL 15+

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/ik4rthik/SwachhLoop-AI.git
cd SwachhLoop-AI

# 2. Create and activate a virtual environment
python -m venv venv

# On Windows (PowerShell):
venv\Scripts\Activate.ps1

# On macOS / Linux:
source venv/bin/activate

# 3. Install runtime dependencies
pip install -r requirements.txt

# 4. (Optional) Install development dependencies
pip install -r requirements-dev.txt
```

### Environment Configuration

```bash
# Copy the template
cp .env.example .env

# Open .env and fill in your values.
# At minimum for Phase 1, the defaults work as-is.
# DATABASE_URL only needs to be correct when Phase 2 DB features are used.
```

Key variables in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment name |
| `DEBUG` | `true` | Enable debug logging and auto-reload |
| `BACKEND_PORT` | `8000` | FastAPI server port |
| `FRONTEND_PORT` | `8501` | Streamlit port |
| `DATABASE_URL` | (see `.env.example`) | PostgreSQL connection string |
| `SECRET_KEY` | `CHANGE_ME_...` | **Must be changed before any deployment** |

### Running the Backend

```bash
# From the project root (with venv activated):
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:

| URL | Description |
|-----|-------------|
| http://localhost:8000 | API root |
| http://localhost:8000/health | Health check endpoint |
| http://localhost:8000/status | Detailed status |
| http://localhost:8000/docs | Interactive Swagger UI |
| http://localhost:8000/redoc | ReDoc documentation |

### Running the Frontend

```bash
# In a separate terminal (with venv activated):
streamlit run frontend/app.py
```

The UI will open at **http://localhost:8501**.

> **Note:** The frontend and backend are independent processes.  
> Start the backend first so the Admin dashboard's health check works.

---

## Development Workflow

```bash
# Run linter
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Run tests
pytest

# Run tests with async support
pytest --asyncio-mode=auto
```

### Typical development loop

1. Create or modify a file in `backend/` or `frontend/`
2. The backend auto-reloads (`--reload` flag in uvicorn)
3. The frontend auto-reloads when you save a file (Streamlit default)
4. Run `ruff check .` before committing

---

## Development Phases

| Phase | Status | Description |
|-------|--------|-------------|
| **Phase 1** | ✅ Complete | Project foundation, structure, config, API skeleton, service interfaces |
| **Phase 2** | 🔲 Planned | Unified frontend — design system, auth UI, role dashboards, complaint forms |
| **Phase 3** | 🔲 Planned | AI agents — waste detection, complaint analysis, Self-Corrective RAG |
| **Phase 4** | 🔲 Planned | Route optimization, cleanup verification, agent orchestration |
| **Phase 5** | 🔲 Planned | Evaluation, guardrails, production hardening |

### Phase 1 Deliverables ✅
- Project structure and clean service boundaries
- Environment configuration (`pydantic-settings`)
- Dependency management (`requirements.txt`)
- Git/GitHub workflow established
- FastAPI backend with `/health`, `/status` endpoints
- Streamlit frontend with role-based routing skeleton
- AI service interface contracts (abstract base classes)
- Full documentation (README + `docs/architecture.md`)

### Phase 2 Scope 🔲
- Shared design system
- Landing page and authentication UI
- Role-based dashboards (full layout)
- Complaint/report interfaces
- Maps and status timelines
- Responsive layout
- Prototype/demo data

---

## Project Principle

SwachhLoop AI is not just a complaint-reporting application. Its objective is a **closed-loop civic workflow** where reported waste is processed, assigned, collected, verified and resolved with accountability.

---

## Repository Workflow

Use feature branches and pull requests. Keep commits focused and avoid mixing unrelated changes. Backend, frontend and AI components should communicate through defined interfaces rather than tightly coupling implementation details.

The project follows a **local-first MVP approach**. Cloud services, WhatsApp integration and MCP are outside the initial MVP scope.
