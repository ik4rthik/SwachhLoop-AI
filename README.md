# SwachhLoop AI

**An Autonomous Multi-Agent System for Closed-Loop Smart Civic Waste Management**

SwachhLoop AI is a civic waste-management platform designed to close the loop from waste reporting to verified resolution.

## Core Workflow

**Report → Validate → Classify → Prioritize → Locate → Optimize → Collect → Verify → Resolve / Escalate**

## Roles

- **Citizen** — report waste, track complaints, view nearby issues and awareness content.
- **Cleaner** — receive assigned cleaning tasks, navigate to locations, submit after-cleanup evidence.
- **Municipal Staff** — manage complaints, priorities, tasks, maps, routes, escalations and analytics.
- **Admin** — manage users, knowledge base, AI monitoring, audit logs and system settings.

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

### AI Components

- Open-source YOLO-family computer vision for waste detection/classification
- LangGraph multi-agent orchestration
- Self-Corrective RAG for knowledge-intensive decisions and awareness generation
- OpenStreetMap with NetworkX / OR-Tools for deterministic route optimization
- Image change detection for cleanup verification
- Cross-cutting guardrails and evaluation

## Technology Stack

- Python
- Streamlit
- FastAPI, Pydantic, Uvicorn
- PostgreSQL / PostGIS (Supabase-compatible)
- ChromaDB
- Open-source embeddings
- Provider-independent LLM interface
- OpenStreetMap
- NetworkX / OR-Tools
- Folium
- Git / GitHub

## Development Strategy

The project follows a local-first MVP approach. Cloud services, WhatsApp integration and MCP are outside the initial MVP scope.

Development is organized into phases, with the frontend and backend using stable service interfaces so AI components can be integrated later without redesigning the application.

## Current Milestone

### Phase 1 — Foundation
- Project structure
- Environment configuration
- Dependency management
- Git/GitHub workflow
- Service boundaries and interfaces

### Phase 2 — Unified Frontend
- Shared design system
- Landing page
- Authentication UI
- Role-based dashboards
- Complaint/report interfaces
- Maps and status timelines
- Responsive layout
- Prototype/demo data

## Project Principle

SwachhLoop AI is not just a complaint-reporting application. Its objective is a **closed-loop civic workflow** where reported waste is processed, assigned, collected, verified and resolved with accountability.

## Repository Workflow

Use feature branches and pull requests. Keep commits focused and avoid mixing unrelated changes. Backend, frontend and AI components should communicate through defined interfaces rather than tightly coupling implementation details.

## Status

🚧 **Active development — Final-year B.Tech AI project**
