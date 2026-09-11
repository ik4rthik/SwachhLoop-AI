# SwachhLoop AI — Architecture Overview

> **Version:** Phase 1 Foundation  
> **Last updated:** September 2026

---

## System Overview

SwachhLoop AI is an autonomous multi-agent system for closed-loop smart civic waste management. Citizens report waste issues via a web interface; AI agents classify, route, and verify cleanup; municipal staff oversee the entire pipeline.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        WEB FRONTEND                             │
│                  (Streamlit — frontend/app.py)                  │
│                                                                 │
│   Citizen UI  │  Cleaner UI  │  Municipal UI  │  Admin UI      │
└───────────────────────────┬─────────────────────────────────────┘
                            │  HTTP (REST)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                       FASTAPI BACKEND                           │
│                    (backend/main.py)                            │
│                                                                 │
│   /health  │  /complaints  │  /cleaners  │  /admin             │
│            (Phase 1)        (Phase 2+)                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
┌─────────────────┐ ┌─────────────┐ ┌──────────────────────────┐
│  SERVICE LAYER  │ │  DATABASE   │ │     AI / AGENT LAYER      │
│ backend/services│ │  backend/db │ │   (Phase 3+ — not yet     │
│                 │ │             │ │    implemented)            │
│ waste_detector  │ │ PostgreSQL  │ │                            │
│ complaint_      │ │ SQLAlchemy  │ │  • Computer Vision (YOLO)  │
│   analyzer      │ │ (async)     │ │  • LangGraph Agents        │
│ route_optimizer │ │             │ │  • Self-Corrective RAG     │
│ cleanup_verifier│ │             │ │  • Route Optimization      │
└─────────────────┘ └─────────────┘ └──────────────────────────┘
```

---

## Directory Structure

```
SwachhLoop-AI/
│
├── backend/                       # FastAPI application
│   ├── main.py                    # App entry point — creates FastAPI, mounts routers
│   ├── api/
│   │   ├── routes/
│   │   │   └── health.py          # /health and /status endpoints (Phase 1 ✅)
│   │   └── dependencies.py        # Shared FastAPI dependencies (auth, db session)
│   ├── core/
│   │   └── config.py              # Pydantic-settings: all env vars in one place
│   ├── models/
│   │   └── schemas.py             # Shared Pydantic request/response schemas
│   ├── services/                  # AI service interfaces (ABCs — Phase 3/4)
│   │   ├── waste_detector.py
│   │   ├── complaint_analyzer.py
│   │   ├── route_optimizer.py
│   │   └── cleanup_verifier.py
│   └── db/
│       └── session.py             # Async SQLAlchemy engine + session factory
│
├── frontend/                      # Streamlit application
│   ├── app.py                     # Entry point — role selector, page routing
│   ├── components/                # Shared UI components (Phase 2+)
│   └── pages/
│       ├── citizen.py             # Citizen dashboard
│       ├── cleaner.py             # Cleaner dashboard
│       ├── municipal_staff.py     # Municipal Staff dashboard
│       └── admin.py               # Admin dashboard + API health check
│
├── docs/
│   └── architecture.md            # This file
│
├── .env.example                   # Environment variable template
├── .gitignore
├── requirements.txt               # Runtime dependencies
├── requirements-dev.txt           # Development/test dependencies
└── README.md                      # Setup and development guide
```

---

## User Roles

| Role | Description |
|------|-------------|
| **Citizen** | Submits waste complaints, tracks resolution status |
| **Cleaner** | Receives assigned tasks, updates status, uploads proof |
| **Municipal Staff** | Reviews complaints, assigns tasks, monitors progress |
| **Admin** | Manages users, system config, monitors AI services |

---

## Service Interfaces (Phase 3/4 Contracts)

Each AI service is defined as a Python Abstract Base Class (ABC). The interface is stable from Phase 1 so that API routes and the agent layer can be written against the interface contract — not against a specific implementation.

| Service | Interface File | Implementation Phase |
|---------|---------------|---------------------|
| Waste Detection | `backend/services/waste_detector.py` | Phase 3 (YOLO / CV model) |
| Complaint Analysis | `backend/services/complaint_analyzer.py` | Phase 3 (LangGraph + LLM) |
| Route Optimization | `backend/services/route_optimizer.py` | Phase 4 (OR-Tools) |
| Cleanup Verification | `backend/services/cleanup_verifier.py` | Phase 4 (CV change detection) |

---

## Development Phases

| Phase | Focus |
|-------|-------|
| **Phase 1** ✅ | Project foundation, structure, config, API skeleton |
| **Phase 2** | Database models, authentication, complaint CRUD |
| **Phase 3** | AI agents — waste detection, complaint analysis, RAG |
| **Phase 4** | Route optimization, cleanup verification, agent orchestration |
| **Phase 5** | Evaluation, guardrails, production hardening |

---

## Key Design Principles

1. **Separation of Concerns** — Frontend never calls the DB or AI directly; everything goes through the API → Service layer.
2. **Interface-First AI** — AI services are defined as ABCs before implementation. This keeps other layers stable.
3. **12-Factor Config** — All configuration is in environment variables, never hardcoded.
4. **Async-First** — SQLAlchemy async engine and FastAPI async routes throughout.
5. **Progressive Enhancement** — Each phase adds capability without redesigning the foundation.
