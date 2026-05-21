# BlackBoxNet

**Live demo:** [https://blackboxnet-web.onrender.com](https://blackboxnet-web.onrender.com)  
**Repository:** [github.com/dkabduli/BlackBoxNet](https://github.com/dkabduli/BlackBoxNet)  
**Author:** Abdul Rehman

A network state replay platform that records configuration snapshots, health metrics, and network events into a Git-backed timeline — like an aircraft black box for network infrastructure.

Replay scripted outages across **Cisco IOS**, **Juniper Junos**, and **Nokia SR OS** labs from one dashboard: step T1→T5, inspect Packet Tracer–style topology (ports, link types, vendor logos), correlate root cause, and diff configs in Git.

## Features

- **Multi-vendor scenarios** — Twelve scripted failure stories across Cisco IOS, Juniper Junos, and Nokia SR OS
- **Header vendor navigation** — Cisco / Juniper / Nokia tabs with vendor logos; only that vendor’s scenarios on the dashboard
- **Scenario catalog** — Short description per scenario on tabs and dashboard title
- **Data-driven topology** — React Flow diagrams from JSON (ports, subnets, link-type legend); layouts: linear, OSPF areas, triangle, Junos, Nokia hub
- **Simulation T1→T5** — Per-scenario state; reset one scenario without touching others
- **Incident timeline & root-cause panel** — Rules-based correlation with vendor-aware semantic diff (ACL, OSPF timers, BGP community, STP priority, LDP label collision, Junos hold-time)
- **Git-backed configs** — Namespaced under `configs/{scenario_id}/{device}/T{n}.txt`
- **Optional live SSH** (Phase 1.5) — One Cisco device can supply real `show running-config` (redacted before storage)
- **Public demo** — Deploy API + static web on Render with Neon Postgres ([docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md))

## Architecture

```
Browser (React 18 + Vite + Tailwind + React Flow)
    → FastAPI + ScenarioManager (12 JSON fixtures)
    → PostgreSQL (scenario_id namespaced rows)
    → Git repo (configs/{scenario_id}/...) — seeded on API startup; ephemeral disk on Render free tier
```

---

## UI navigation

| Location | What you pick |
|----------|----------------|
| **Header** (next to BlackBoxNet) | Vendor platform: **Cisco** (IOS), **Juniper** (Junos), **Nokia** (SR OS) |
| **Dashboard** (below title) | Scenario within that vendor (e.g. ACL Regression, LDP Collision) |
| **Simulation card** | Run **T1** … **T5** or **Reset** for the active scenario only |

Switching vendor in the header loads that vendor’s scenario list and selects its first scenario. **Each vendor or scenario tab click resets the target scenario to T1** (with a confirmation if the current scenario has progress). Devices, topology, incidents, and simulation progress are all scoped to `scenario_id`.

---

## Phase 2: Multi-scenario library (12 scenarios)

### Cisco IOS (`vendor_group: cisco`)

| ID | Label | Layout | Root cause (T5) |
|----|-------|--------|-----------------|
| `acl-regression` | ACL Regression | `linear` | ACL deny blocks `10.0.1.0/24` |
| `ospf-multiarea` | OSPF Multi-Area | `ospf-areas` | Hello/dead timer mismatch (R1) |
| `bgp-route-leak` | BGP Leak | `triangle` | `no-export` stripped on eBGP export |
| `stp-root-hijack` | STP Root Hijack | `star` / `hub` | Rogue bridge priority 0 |

### Juniper Junos (`vendor_group: juniper`)

| ID | Label | Layout | Root cause (T5) |
|----|-------|--------|-----------------|
| `juniper-bgp-hold` | BGP Hold Timer | `junos-triangle` | hold-time 30 vs peer 90 |
| `juniper-isis-metric` | IS-IS Wide Metric | `junos-triangle` | Wide metric on PE→CE |
| `juniper-rsvp-te` | RSVP-TE LSP | `junos-triangle` | RSVP bandwidth on 10G LSP |
| `juniper-firewall-policer` | SRX Policer | `junos-triangle` | Policer drops voice traffic |

### Nokia SR OS (`vendor_group: nokia`)

| ID | Label | Layout | Root cause (T5) |
|----|-------|--------|-----------------|
| `nokia-ldp-collision` | LDP Collision | `nokia-hub` | Static label 131071 LFIB overwrite |
| `nokia-sdp-blackhole` | SDP Blackhole | `nokia-hub` | Spoke-SDP points to wrong VC |
| `nokia-vprn-leak` | VPRN Leak | `nokia-hub` | Export policy leaks VPRN 200 into 100 |
| `nokia-qos-policer` | QoS Policer | `nokia-hub` | Ingress policer on 10G access |

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
- **Rendered by:** `apps/web/src/components/topology/LazyTopologyPreview.tsx` (code-split React Flow)

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
| `layout` | `linear`, `ospf-areas`, `triangle`, `junos-triangle`, `nokia-hub`, `hub`, `star` |
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

#### Juniper layouts (`junos-triangle`)

Used by BGP hold, IS-IS metric, RSVP-TE, and SRX policer scenarios. Preset positions for `edge-router`, `rr-1`, `pe-1`, `p-1`, `ingress-pe`, `transit-p`, `egress-pe`, `ce-1`; terminals `_users` / `_fec` at the bottom. Annotations describe each failure (hold-time mismatch, policer loss, etc.).

#### Nokia layouts (`nokia-hub`)

Hub node defaults to `p-router` (override with `topology.hub`). Spokes `pe-1`, `pe-2`, `pe-agg`, `pe-access`; terminals `_fec`, `_users`, `_sdp`. Used by LDP collision, SDP blackhole, VPRN leak, and QoS policer scenarios.

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

### Live demo (Render + Neon)

| Service | URL |
|---------|-----|
| **Web — use this on your resume** | [blackboxnet-web.onrender.com](https://blackboxnet-web.onrender.com) |
| API | [blackboxnet-api.onrender.com](https://blackboxnet-api.onrender.com) |
| API docs | [blackboxnet-api.onrender.com/docs](https://blackboxnet-api.onrender.com/docs) |

**Cold start:** On the free tier the API sleeps after ~15 minutes idle. The first **Run T1** may take **30–60 seconds** — leave the tab open and wait once, then run T1→T5.

**Quick walkthrough:** Cisco → ACL Regression → T1→T5 → open incident → config diff. Switch **Juniper** / **Nokia** in the header for other topologies (confirmation appears if you have progress on the current scenario).

**Deploy / env:** [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md). Postgres persists in Neon; Git config on the API disk is ephemeral across redeploys (bundled configs seed on startup).

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
│           │   ├── topology/        # LazyTopologyPreview, React Flow layouts
│           │   └── simulation/      # SimulationControls, ScenarioTabBar
│           ├── context/             # ScenarioContext (vendor + scenario)
│           └── lib/vendorGroups.ts
├── packages/mock-scenarios/
│   ├── topology-presets.json        # topology source of truth
│   ├── *.json                       # twelve scenario fixtures
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
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, React Flow, dagre |
| Backend | Python 3.11, FastAPI, SQLAlchemy 2, Alembic |
| Database | PostgreSQL 15 |
| VCS | Git (GitPython) |
| Infra | Docker Compose; optional Render + Neon |

## Further reading

- [docs/DEMO_SCRIPT.md](docs/DEMO_SCRIPT.md) — 5-minute interview walkthrough
- [docs/DEPLOY_RENDER.md](docs/DEPLOY_RENDER.md) — free public hosting
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — system design notes
- [docs/SCENARIO_DEFINITION.md](docs/SCENARIO_DEFINITION.md) — scenario JSON format

## Testing

Backend: `cd apps/api && pip install -r requirements-dev.txt && pytest` — scenario loading, DB URLs, correlation, semantic extractors, config Git, simulation guards.

Frontend: `cd apps/web && npm run build` — TypeScript compile and production bundle (CI runs on every push to `main`).
