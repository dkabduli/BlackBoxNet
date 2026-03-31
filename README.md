# BlackBoxNet

A network state replay platform that records configuration snapshots, health metrics, and network events into a Git-backed timeline. Like an aircraft black box for network infrastructure.

## Phase 1: Simulation-Driven MVP

Phase 1 simulates a small network (3 devices), records state over time, stores config versions in Git, and lets users replay one realistic outage scenario (ACL regression) with rules-based correlation.

### Features

- **Device Dashboard** — View three simulated network devices with real-time health metrics (CPU, memory, latency, packet loss)
- **Topology Preview** — Compact path diagram with ports, addressing, and root-cause highlighting during incidents
- **Incident Timeline** — Chronological event visualization from healthy baseline through outage
- **Root Cause Panel** — Direct incident-page shortcut to the suspect config mismatch and diff viewer
- **Config Diff Viewer** — Side-by-side config diffs with semantic analysis highlighting the ACL change
- **Correlation Engine** — Rules-based analysis linking config changes to outage events
- **Git-backed Config History** — All config snapshots stored in a real Git repository
- **Simulation Controls** — Step through T1→T5 scenario progression

### Architecture

```
Frontend (React + Vite + Tailwind)  →  API (FastAPI + SQLAlchemy)  →  PostgreSQL + Git
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for local frontend dev)
- Python 3.11+ (for local backend dev)

### Running with Docker Compose

```bash
docker-compose up -d
```

- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

**5-minute demo (interviews / reviews):** see [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

### Local Development

**Backend:**

```bash
cd apps/api
pip install -r requirements.txt

# Start PostgreSQL
docker-compose up db -d

# Set env vars
export DATABASE_URL="postgresql+asyncpg://blackboxnet:blackboxnet_dev@localhost:5432/blackboxnet"
export DATABASE_URL_SYNC="postgresql://blackboxnet:blackboxnet_dev@localhost:5432/blackboxnet"
export GIT_REPO_PATH="./data/config-repo"
export SCENARIO_PATH="../../packages/mock-scenarios/acl-regression.json"

# Run migrations
alembic upgrade head

# Start API
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd apps/web
npm install
npm run dev
```

## Usage

1. Open the Dashboard at http://localhost:3000
2. Click **Run T1** to collect the healthy baseline
3. Click **Run T2** — a config change (ACL modification) is applied
4. Click **Run T3** — degradation events (latency spike, packet loss) appear
5. Click **Run T4** — interface degradation and CPU rise detected
6. Click **Run T5** — outage detected, incident created with correlation analysis
7. Click the incident to view the topology highlight, root-cause panel, full timeline, and config diff
8. Click **Reset** to start over

### Demo Flow

- The simulation card shows the path under test directly under **Simulation**
- `T1` through `T5` stay visible as the incident replay checkpoints
- The topology preview highlights the suspected root device once an incident exists
- The incident detail page exposes a direct **View Root Cause Diff** action

### Verification

Backend tests:

```bash
cd apps/api
pip install -r requirements-dev.txt
pytest
```

Frontend build:

```bash
cd apps/web
npm install
npm run build
```

## Project Structure

```
BlackBoxNet/
├── apps/
│   ├── api/                    # FastAPI backend
│   │   ├── app/
│   │   │   ├── api/routes/     # REST API endpoints
│   │   │   ├── core/           # Scenario engine, semantic extraction
│   │   │   ├── models/         # SQLAlchemy ORM models
│   │   │   ├── schemas/        # Pydantic request/response schemas
│   │   │   ├── services/       # Business logic services
│   │   │   └── main.py         # FastAPI application
│   │   ├── alembic/            # Database migrations
│   │   └── requirements.txt
│   └── web/                    # React frontend
│       └── src/
│           ├── api/            # API client
│           ├── components/     # Reusable UI components
│           ├── pages/          # Page components
│           └── types/          # TypeScript type definitions
├── packages/
│   └── mock-scenarios/         # Scenario JSON + config files
├── docs/                       # Specification documents
└── docker-compose.yml
```

## Tech Stack

| Layer      | Technology                          |
|------------|-------------------------------------|
| Frontend   | React 18, TypeScript, Vite, Tailwind CSS |
| Backend    | Python 3.11, FastAPI, SQLAlchemy 2  |
| Database   | PostgreSQL 15                        |
| VCS        | Git (via GitPython)                  |
| Infra      | Docker Compose                       |
