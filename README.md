# BlackBoxNet

A network state replay platform that records configuration snapshots, health metrics, and network events into a Git-backed timeline — like an aircraft black box for network infrastructure.

Replay scripted outages across **Cisco IOS**, **Juniper Junos**, and **Nokia SR OS** labs from one dashboard: step T1→T5, inspect topology with real port labels, correlate root cause, and diff configs in Git.

## Features

- **Multi-vendor scenarios** — Six independent failure stories (ACL, OSPF, BGP, STP, Juniper hold-timer, Nokia LDP collision)
- **Header vendor navigation** — Cisco / Juniper / Nokia beside the logo; only that vendor’s scenarios show on the dashboard
- **Data-driven topology** — Each scenario declares links (ports, subnets, types); UI renders layout-specific diagrams
- **Simulation T1→T5** — Per-scenario state; reset one scenario without touching others
- **Incident timeline & root-cause panel** — Rules-based correlation with vendor-aware semantic diff (ACL, OSPF timers, BGP community, STP priority, LDP label collision, Junos hold-time)
- **Git-backed configs** — Namespaced under `configs/{scenario_id}/{device}/T{n}.txt`
- **Optional live SSH** (Phase 1.5) — One Cisco device can supply real `show running-config` (redacted before storage)
- **Public demo** — Deploy API + static web on Render with Neon Postgres ([docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md))

## Architecture

```
Browser (React + Vite + Tailwind)
    → FastAPI + ScenarioManager (6 JSON fixtures)
    → PostgreSQL (scenario_id namespaced rows)
    → Git repo (configs/{scenario_id}/...)
```

---

## UI navigation

| Location | What you pick |
|----------|----------------|
| **Header** (next to BlackBoxNet) | Vendor platform: **Cisco** (IOS), **Juniper** (Junos), **Nokia** (SR OS) |
| **Dashboard** (below title) | Scenario within that vendor (e.g. ACL Regression, LDP Collision) |
| **Simulation card** | Run **T1** … **T5** or **Reset** for the active scenario only |

Switching vendor in the header loads that vendor’s scenario list and selects its first scenario. **Each vendor or scenario tab click resets that scenario to T1** (API `POST /api/simulation/reset?scenario_id=` + cleared devices/incidents for that scenario only). Devices, topology, incidents, and simulation progress are all scoped to `scenario_id`.

---

## Phase 2: Multi-scenario library

| Vendor | Scenario ID | Label | Root cause (T5) | Devices |
|--------|-------------|-------|-------------------|---------|
| Cisco IOS | `acl-regression` | ACL Regression | ACL deny blocks `10.0.1.0/24` | edge-router-1, dist-switch-1, access-switch-1 |
| Cisco IOS | `ospf-multiarea` | OSPF Multi-Area | Hello/dead timer mismatch on R1 | R1–R4 (ABRs + IRs) |
| Cisco IOS | `bgp-route-leak` | BGP Leak | `no-export` stripped on eBGP export | edge-router-1, core-router-1, rr-1 |
| Cisco IOS | `stp-root-hijack` | STP Root Hijack | Rogue bridge priority 0 | core-1, dist-1/2, access-1, rogue-1 |
| Juniper Junos | `juniper-bgp-hold` | BGP Hold Timer | hold-time 30 vs peer 90 | edge-router, rr-1, pe-1 |
| Nokia SR OS | `nokia-ldp-collision` | LDP Collision | Static label 131071 LFIB overwrite | p-router, pe-1, pe-2 |

**API (scenario-scoped):**

| Endpoint | Purpose |
|----------|---------|
| `GET /api/scenarios` | Catalog with `topology`, `vendor_group`, `step_labels` |
| `GET /api/simulation/status?scenario_id=` | Progress, devices, step labels |
| `POST /api/simulation/run-step?scenario_id=` | Collect snapshot + events |
| `POST /api/simulation/reset?scenario_id=` | Wipe DB + Git namespace for one scenario |
| `GET /api/diff/{scenario_id}/{device_id}` | Unified diff between last two Git snapshots |

**Regenerate all scenario JSON + config snapshots:**

```bash
python3 scripts/generate_phase2_scenarios.py
```

---

## Topology system

Topology is **declarative**, not hardcoded in React. Definitions live in:

- **Primary:** `packages/mock-scenarios/topology-presets.json`
- **Copied into:** each `packages/mock-scenarios/{scenario-id}.json` under `"topology"` when you run the generator
- **Served by API:** `GET /api/scenarios` → each item includes a `topology` object
- **Rendered by:** `apps/web/src/components/topology/TopologyPreview.tsx`

### Link schema

Each entry in `topology.links[]`:

| Field | Description |
|-------|-------------|
| `from` | Source device hostname |
| `to` | Target hostname, or `_users` / `_fec` for terminal endpoints |
| `left_port` | Port/interface on the `from` side |
| `right_port` | Port/interface on the `to` side |
| `subnet` | Circuit, VLAN, FEC, or impacted prefix label |
| `type` | `routed`, `trunk`, `serial`, `ldp`, `ibgp`, `ebgp`, `ospf-backbone`, `rogue-uplink`, etc. |
| `area` | OSPF area label (multi-area layout) |
| `terminal` | If `true`, render users/FEC endpoint (not a router node) |

Optional topology fields:

| Field | Used by |
|-------|---------|
| `layout` | Renderer: `linear`, `ospf-areas`, `hub`, `triangle`, `star` |
| `hub` | Center node for `hub` and `star` layouts |
| `affected_subnet` | Blue “Impacted: …” badge on the diagram |
| `annotations[]` | Context lines (e.g. rogue STP switch, LFIB collision) |

Device nodes on the diagram use **live API data**: hostname, `management_ip`, role, health color, and **root-cause** highlight when an incident points at that device.

### Per-scenario topology

#### Cisco — ACL Regression (`linear`)

```
edge-router-1 —Gi0/0↔Gi0/1— dist-switch-1 —Gi0/2↔Gi0/1— access-switch-1 —Gi0/24— users (10.0.1.0/24)
```

| Link | Ports | Subnet / type |
|------|-------|----------------|
| edge → dist | Gi0/0 ↔ Gi0/1 | 10.0.0.0/24 transit · routed |
| dist → access | Gi0/2 ↔ Gi0/1 | 802.1Q trunk |
| access → users | Gi0/24 ↔ users | 10.0.1.0/24 · access (terminal) |

#### Cisco — OSPF Multi-Area (`ospf-areas`)

```
        R1 —Area 0— R2
         |           |
    Se0/0/0     Se0/0/0
         |           |
        R3          R4
     Area 1 IR    Area 2 IR
```

| Link | Ports | Notes |
|------|-------|-------|
| R1 ↔ R2 | Area 0 | Backbone |
| R1 ↔ R3 | Se0/0/0 | Area 1 · 10.1.0.0/24 |
| R2 ↔ R4 | Se0/0/0 | Area 2 · 10.2.0.0/24 |

#### Cisco — BGP Route Leak (`triangle`)

Triangle between `edge-router-1`, `core-router-1`, `rr-1` with iBGP and eBGP upstream edges (Gi0/x labeled per link).

#### Cisco — STP Root Hijack (`star`)

Hub: `core-1` with trunks to `dist-1`, `dist-2`; access path to `access-1`; separate **rogue-1** uplink to `dist-2` (TCN ingress).

#### Juniper — BGP Hold Timer (`triangle`)

`edge-router` ↔ `rr-1` (eBGP) ↔ `pe-1` (iBGP); service path `lo0` for `10.0.10.0/24`. Annotation: hold-time 30 vs peer 90.

#### Nokia — LDP Collision (`hub`)

Hub: `p-router` with LDP sessions to `pe-1` and `pe-2` (`toPE1` / `toPE2`). Terminal FEC: **10.0.1.0/24 (label 131071)**. Annotation: SR7750 LFIB collision point.

### Editing topology

1. Edit `packages/mock-scenarios/topology-presets.json`
2. Run `python3 scripts/generate_phase2_scenarios.py`
3. Restart API (or rely on volume mount + reload) and refresh the browser

No React changes are required for new links or port labels if the layout already exists.

---

## Git config layout

```
configs/
  acl-regression/
    edge-router-1/   T1.txt … T5.txt
    dist-switch-1/   T1.txt … T5.txt
    access-switch-1/ T1.txt … T5.txt
  ospf-multiarea/
    R1/ … R4/
  nokia-ldp-collision/
    p-router/ pe-1/ pe-2/
  bgp-route-leak/
  stp-root-hijack/
  juniper-bgp-hold/
```

Commits are tagged in messages with `[scenario_id]`. Resetting a scenario removes only that folder under `configs/` in the Git repo.

---

## Phase 1 & Phase 1.5 (foundation)

**Phase 1** introduced the first ACL regression story: three devices, T1→T5 timeline, correlation engine, and diff viewer.

**Phase 1.5** adds optional hybrid collection: one configured device can pull live Cisco config over SSH while metrics and timeline remain simulated. Secrets are redacted before Git or API exposure.

```bash
REAL_DEVICE_ENABLED=true
REAL_DEVICE_HOST=192.0.2.10
REAL_DEVICE_SCENARIO_DEVICE_ID=edge-router-1
# see apps/api/.env.example
```

---

## Quick start

### Prerequisites

- Docker & Docker Compose
- Node.js 18+ (local frontend)
- Python 3.11+ (local backend)

### Docker Compose (recommended)

```bash
docker compose up -d --build
```

| Service | URL |
|---------|-----|
| Web | http://localhost:3000 |
| API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

Migrations run on API startup (`001` schema + `002` `scenario_id` namespacing).

### Demo flow

1. Open the dashboard — pick **Cisco**, **Juniper**, or **Nokia** in the header (resets that vendor’s default scenario to T1).
2. Pick a **scenario** tab (e.g. ACL Regression) — also resets to T1 before you run steps.
3. Click **Run T1** … **Run T5** on the simulation card.
4. Open the **incident** for timeline, root-cause summary, and config diff.
5. **Reset** replays only the active scenario from T1.

Full script: [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md).

### Live public demo (Render + Neon, $0)

One GitHub repo → portfolio link. See [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md). Share the **web** URL; note that free-tier API cold start can take 30–60 seconds after idle.

### Local development

**Backend:**

```bash
cd apps/api
pip install -r requirements.txt
docker compose up db -d

export DATABASE_URL="postgresql+asyncpg://blackboxnet:blackboxnet_dev@localhost:5432/blackboxnet"
export DATABASE_URL_SYNC="postgresql://blackboxnet:blackboxnet_dev@localhost:5432/blackboxnet"
export GIT_REPO_PATH="./data/config-repo"
export SCENARIOS_DIR="../../packages/mock-scenarios"

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend:**

```bash
cd apps/web
npm install
npm run dev
```

### Verification

```bash
cd apps/api && pip install -r requirements-dev.txt && pytest
cd apps/web && npm run build
```

---

## Project structure

```
BlackBoxNet/
├── apps/
│   ├── api/
│   │   ├── app/
│   │   │   ├── api/routes/          # devices, incidents, simulation, scenarios
│   │   │   ├── core/
│   │   │   │   ├── scenario_engine.py
│   │   │   │   ├── scenario_manager.py   # loads all *.json + topology presets
│   │   │   │   └── semantic_extraction/  # cisco_ios, nokia_sros, junos
│   │   │   └── services/            # collector, correlation, config_git, diff
│   │   └── alembic/versions/        # 001 schema, 002 scenario_id
│   └── web/
│       └── src/
│           ├── components/
│           │   ├── layout/          # VendorNav (header), Layout
│           │   ├── topology/        # TopologyPreview (layout renderers)
│           │   └── simulation/      # SimulationControls, ScenarioTabBar
│           ├── context/             # ScenarioContext (vendor + scenario)
│           └── lib/vendorGroups.ts
├── packages/mock-scenarios/
│   ├── topology-presets.json        # topology source of truth
│   ├── *.json                       # six scenario fixtures
│   └── configs/{scenario_id}/       # per-device T1–T5 configs
├── scripts/generate_phase2_scenarios.py
├── docs/                            # DEMO_SCRIPT, DEPLOY_RENDER, PRD, …
├── render.yaml                      # Render blueprint
└── docker-compose.yml
```

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2, Alembic |
| Database | PostgreSQL 15 |
| VCS | Git (GitPython) |
| Infra | Docker Compose; optional Render + Neon |

## Further reading

- [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) — 5-minute interview walkthrough
- [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md) — free public hosting
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design notes
- [docs/SCENARIO_DEFINITION.md](docs/SCENARIO_DEFINITION.md) — scenario JSON format
