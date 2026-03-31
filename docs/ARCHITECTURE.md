# BlackBoxNet - System Architecture
## Phase 1 Architecture Design

**Version:** 1.0  
**Date:** 2024-11-15  
**Status:** Implementation Ready

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [System Components](#system-components)
3. [Data Flow](#data-flow)
4. [Technology Stack](#technology-stack)
5. [Component Details](#component-details)
6. [Integration Points](#integration-points)
7. [Deployment Architecture](#deployment-architecture)
8. [Future Extensibility](#future-extensibility)

---

## Architecture Overview

### Design Principles

1. **Separation of Concerns**
   - Clear boundaries between simulation, data persistence, correlation, and presentation
   - Each component has a single responsibility

2. **Future-Proof Design**
   - Easy to swap mock simulation for real device polling in Phase 2
   - Vendor abstraction layer ready for multi-vendor support
   - Extensible event and correlation engines

3. **Git as First-Class Citizen**
   - Config history lives in real Git repository
   - Enables future features: branching, rollback, compliance tracking

4. **Timeline-Centric**
   - All data organized by timestamp
   - Events are immutable records
   - Replay is a core capability, not an afterthought

---

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Frontend (React)                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Dashboard   │  │   Incident   │  │   Timeline   │          │
│  │    View      │  │   Detail     │  │    Replay    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Service (FastAPI)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Devices    │  │  Incidents   │  │   Configs    │          │
│  │   Endpoints  │  │  Endpoints   │  │   Endpoints  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   PostgreSQL  │  │  Git Repo     │  │  Scenario     │
│   Database    │  │  (configs)    │  │  Engine       │
└───────────────┘  └───────────────┘  └───────────────┘
                                               │
                                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Background Services                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  Collector   │  │    Event     │  │ Correlation  │          │
│  │  Service     │  │   Engine     │  │   Engine     │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐  ┌──────────────┐                            │
│  │ Config Git   │  │    Diff      │                            │
│  │  Service     │  │   Engine     │                            │
│  └──────────────┘  └──────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

---

## System Components

### 1. Mock Scenario Engine

**Purpose:** Provides time-based network state for simulation

**Responsibilities:**
- Load scenario definition from JSON
- Expose device state at each time step
- Simulate state transitions deterministically
- Provide device configs, metrics, and interface states

**Phase 1 Implementation:**
- Single scenario: ACL regression
- Time steps: T1 (0s), T2 (60s), T3 (120s), T4 (180s), T5 (240s)
- State stored in JSON with interpolated values

**Interface:**
```python
class ScenarioEngine:
    def load_scenario(scenario_path: str) -> None
    def get_device_state(device_id: str, timestamp: int) -> DeviceState
    def get_all_devices_state(timestamp: int) -> List[DeviceState]
    def advance_time() -> int  # Returns new timestamp
    def get_current_time() -> int
    def reset() -> None
```

---

### 2. Collector Service

**Purpose:** Consumes device state and persists snapshots

**Responsibilities:**
- Poll scenario engine for current state (simulates polling real devices)
- Create snapshot records in database
- Create interface snapshot records
- Trigger config Git service on config changes
- Run on schedule or manual trigger

**Phase 1 Implementation:**
- Manual trigger via API endpoint: `POST /simulation/run-step`
- Collects all three devices per step
- Detects config hash changes

**Interface:**
```python
class CollectorService:
    def collect_snapshot(device_id: str) -> Snapshot
    def collect_all_devices() -> List[Snapshot]
    def detect_config_change(device_id: str, new_hash: str) -> bool
```

---

### 3. Snapshot Processor

**Purpose:** Process and store device state snapshots

**Responsibilities:**
- Persist snapshot to database
- Persist interface snapshots
- Calculate deltas from previous snapshot
- Return snapshot metadata for downstream services

**Database Operations:**
- Insert into `snapshots` table
- Insert into `interface_snapshots` table
- Query previous snapshot for delta calculation

---

### 4. Config Git Service

**Purpose:** Manage configuration versioning in Git

**Responsibilities:**
- Write config to filesystem at structured path
- Create Git commit when config changes
- Generate commit messages
- Provide Git log access
- Track config versions in database

**Git Repository Structure:**
```
data/config-repo/
├── edge-router-1/
│   ├── 2024-11-15T10-22-00.cfg
│   ├── 2024-11-15T10-23-45.cfg  ← Config change at T2
│   └── latest.cfg → symlink to latest
├── dist-switch-1/
│   └── 2024-11-15T10-22-00.cfg
└── access-switch-1/
    └── 2024-11-15T10-22-00.cfg
```

**Commit Strategy:**
- One commit per collection cycle
- Commit includes all changed device configs
- Commit message format: `config snapshot: 2024-11-15T10:23:45Z | changed: edge-router-1`

**Interface:**
```python
class ConfigGitService:
    def write_config(device_id: str, config: str, timestamp: datetime) -> str
    def commit_changes(timestamp: datetime, changed_devices: List[str]) -> str
    def get_commit_history(device_id: str) -> List[GitCommit]
    def get_config_at_commit(device_id: str, commit_hash: str) -> str
```

---

### 5. Diff Engine

**Purpose:** Generate configuration diffs and semantic summaries

**Responsibilities:**
- Compare two config versions (text diff)
- Extract semantic changes (ACL modifications, interface changes, etc.)
- Generate human-readable summary
- Store diff in database

**Diff Types:**
1. **Raw Text Diff:** Standard unified diff format
2. **Semantic Diff:** Structured JSON of extracted changes

**Interface:**
```python
class DiffEngine:
    def generate_diff(old_config: str, new_config: str) -> ConfigDiff
    def extract_semantic_changes(diff_text: str, vendor: str) -> List[SemanticChange]
    def summarize_changes(semantic_changes: List[SemanticChange]) -> str
```

**Semantic Change Structure:**
```python
@dataclass
class SemanticChange:
    change_type: str  # ACL_MODIFIED, INTERFACE_ACL_BINDING, etc.
    entity: str       # access-list 101, GigabitEthernet0/0
    action: str       # added, removed, modified
    details: dict     # change-specific details
    suspicion_level: str  # low, medium, high
    reason: str       # why this is suspicious
```

---

### 6. Event Engine

**Purpose:** Detect state changes and emit events

**Responsibilities:**
- Compare snapshots to detect deltas
- Apply threshold rules to trigger events
- Create event records in database
- Assign severity and metadata

**Event Detection Rules (Phase 1):**

```python
# CONFIG_CHANGE
if snapshot.config_hash != previous_snapshot.config_hash:
    emit_event(EventType.CONFIG_CHANGE, severity=INFO)

# LATENCY_SPIKE
if snapshot.latency_ms > 50 and previous_snapshot.latency_ms < 30:
    emit_event(EventType.LATENCY_SPIKE, severity=WARNING)

# PACKET_LOSS_INCREASE
if snapshot.packet_loss_pct > 20 and previous_snapshot.packet_loss_pct < 10:
    emit_event(EventType.PACKET_LOSS_INCREASE, severity=WARNING)

# INTERFACE_DEGRADED
if snapshot.interface.rx_errors > previous.interface.rx_errors + 1000:
    emit_event(EventType.INTERFACE_DEGRADED, severity=ERROR)

# CPU_RISE
if snapshot.cpu_usage > 70 and previous_snapshot.cpu_usage < 40:
    emit_event(EventType.CPU_RISE, severity=WARNING)

# OUTAGE_STARTED
if snapshot.packet_loss_pct >= 80:
    emit_event(EventType.OUTAGE_STARTED, severity=CRITICAL)
```

**Interface:**
```python
class EventEngine:
    def detect_events(snapshot: Snapshot, previous: Snapshot) -> List[Event]
    def emit_event(event_type: EventType, device_id: str, **kwargs) -> Event
```

---

### 7. Correlation Engine

**Purpose:** Apply rules-based correlation to identify suspicious changes

**Responsibilities:**
- Find recent config changes before outages
- Analyze semantic diffs for relevant changes
- Generate suspicion summaries
- Create correlation flag events
- Update incident suspicion metadata

**Correlation Rules (Phase 1):**

```python
# Rule A: Recent Config Change Before Degradation
def rule_recent_config_change_before_degradation(incident):
    config_changes = get_config_changes_in_window(incident, window=300s)
    degradation_events = get_degradation_events(incident)
    
    for config_change in config_changes:
        if any(deg.timestamp > config_change.timestamp for deg in degradation_events):
            return CorrelationFlag(
                suspicion="Config change preceded degradation",
                evidence=[config_change.id, degradation_events[0].id]
            )

# Rule B: ACL-Related Suspicion
def rule_acl_deny_affects_subnet(incident, affected_subnet):
    config_changes = get_config_changes(incident)
    
    for change in config_changes:
        semantic = get_semantic_diff(change)
        
        for sem_change in semantic:
            if sem_change.change_type == "ACL_MODIFIED":
                if affected_subnet in sem_change.details.get("denied_subnets", []):
                    return CorrelationFlag(
                        suspicion="ACL deny rule affects outage subnet",
                        evidence=[change.id],
                        suspicion_level="high"
                    )

# Rule C: Time-Ordered Primary Suspect
def rule_first_change_primary_suspect(incident):
    all_events = get_timeline_events(incident)
    config_changes = [e for e in all_events if e.event_type == "CONFIG_CHANGE"]
    
    if config_changes:
        first_change = min(config_changes, key=lambda e: e.timestamp)
        return CorrelationFlag(
            suspicion="First config change is primary suspect",
            evidence=[first_change.id],
            suspicion_level="high"
        )
```

**Interface:**
```python
class CorrelationEngine:
    def correlate_incident(incident_id: str) -> IncidentCorrelation
    def apply_rules(incident: Incident) -> List[CorrelationFlag]
    def generate_suspicion_summary(flags: List[CorrelationFlag]) -> str
```

---

### 8. API Service (FastAPI)

**Purpose:** Expose REST API for frontend

**Responsibilities:**
- Serve device data
- Serve incident data
- Serve timeline events
- Serve config diffs
- Trigger simulation steps
- Handle CORS for frontend

**Core Endpoints:**

```
GET  /api/devices
GET  /api/devices/{device_id}
GET  /api/devices/{device_id}/health
GET  /api/devices/{device_id}/snapshots
GET  /api/devices/{device_id}/config/versions
GET  /api/devices/{device_id}/config/diff/{diff_id}

GET  /api/incidents
GET  /api/incidents/{incident_id}
GET  /api/incidents/{incident_id}/timeline
GET  /api/incidents/{incident_id}/correlation

POST /api/simulation/run-step
POST /api/simulation/reset
GET  /api/simulation/status
```

**See API_SPEC.md for full OpenAPI specification**

---

### 9. Web Frontend (React)

**Purpose:** User interface for visualization and interaction

**Responsibilities:**
- Display device dashboard
- Display incident list and details
- Render timeline with event cards
- Show config diffs with syntax highlighting
- Provide step-through navigation
- Trigger simulation advancement

**Key Pages:**
- `/` – Dashboard (device overview + incident cards)
- `/devices` – Device list with health details
- `/devices/:id` – Device detail page
- `/incidents` – Incident list
- `/incidents/:id` – Incident detail with timeline
- `/incidents/:id/timeline/:event_id` – Event detail view

**Key Components:**
- `DeviceCard` – Shows device status and metrics
- `IncidentCard` – Shows incident summary
- `Timeline` – Vertical event timeline
- `EventDetail` – Drawer/panel for event details
- `ConfigDiff` – Side-by-side diff viewer
- `CorrelationSummary` – Suspicion display

---

## Data Flow

### Scenario Execution Flow

```
1. User triggers simulation step
   │
   ├─→ POST /api/simulation/run-step
   │
2. API calls CollectorService.collect_all_devices()
   │
   ├─→ CollectorService queries ScenarioEngine for current state
   │   ├─→ ScenarioEngine returns device states at current_time
   │
   ├─→ For each device:
   │   ├─→ SnapshotProcessor.persist_snapshot(device_state)
   │   │   ├─→ Inserts snapshot into DB
   │   │   ├─→ Inserts interface_snapshots into DB
   │   │
   │   ├─→ If config_hash changed:
   │   │   ├─→ ConfigGitService.write_config()
   │   │   ├─→ ConfigGitService.commit_changes()
   │   │   ├─→ DiffEngine.generate_diff()
   │   │   ├─→ Store config_diff in DB
   │   │
   │   ├─→ EventEngine.detect_events(snapshot, previous_snapshot)
   │   │   ├─→ Apply detection rules
   │   │   ├─→ Emit events to DB
   │   │
   │   ├─→ If OUTAGE_STARTED event:
   │       ├─→ Create incident in DB
   │       ├─→ CorrelationEngine.correlate_incident()
   │           ├─→ Apply correlation rules
   │           ├─→ Generate suspicion summary
   │           ├─→ Update incident with suspicion
   │
3. ScenarioEngine.advance_time()
   │
4. Return new state to API
   │
5. API returns updated status to frontend
   │
6. Frontend refreshes dashboard/timeline
```

---

### Timeline Query Flow

```
1. User opens incident detail page
   │
   ├─→ GET /api/incidents/{id}/timeline
   │
2. API queries database:
   │
   ├─→ SELECT * FROM events WHERE device_id IN (incident.affected_devices)
   │   ORDER BY timestamp ASC
   │
   ├─→ For each CONFIG_CHANGE event:
   │   ├─→ Join with config_diffs table
   │   ├─→ Include diff_id for linking
   │
3. API returns event array to frontend
   │
4. Frontend renders Timeline component
   │
5. User clicks event
   │
   ├─→ If CONFIG_CHANGE:
   │   ├─→ GET /api/devices/{device_id}/config/diff/{diff_id}
   │   ├─→ API returns diff text + semantic summary
   │   ├─→ Frontend renders ConfigDiff component
   │
   ├─→ If other event:
       ├─→ Display event details in drawer
       ├─→ Show related metrics
```

---

## Technology Stack

### Backend

**Language:** Python 3.11+

**Framework:** FastAPI 0.104+
- Async support
- Automatic OpenAPI generation
- Type hints with Pydantic
- High performance

**ORM:** SQLAlchemy 2.0+
- Database migrations via Alembic
- Type-safe queries
- Async support

**Database:** PostgreSQL 15+
- JSONB support for metadata
- Strong consistency
- Excellent indexing

**Git Library:** GitPython 3.1+
- Pure Python implementation
- Easy to use
- Good documentation

**Additional Libraries:**
- `pydantic` – Data validation
- `python-dateutil` – Date/time handling
- `difflib` – Built-in diff generation
- `pytest` – Testing

---

### Frontend

**Framework:** React 18+
- Component-based architecture
- Hooks for state management
- Large ecosystem

**Build Tool:** Vite
- Fast HMR
- Modern ES modules
- Better DX than CRA

**UI Library:** shadcn/ui + Tailwind CSS
- Accessible components
- Customizable
- No runtime overhead (copies components)
- Utility-first CSS

**State Management:** React Context + Hooks
- Simple for Phase 1 scope
- No external library needed
- Easy to upgrade to Zustand/Redux later

**Routing:** React Router v6
- Declarative routing
- Nested routes
- URL state management

**Additional Libraries:**
- `react-diff-view` – Diff visualization
- `date-fns` – Date formatting
- `axios` – HTTP client
- `react-syntax-highlighter` – Config syntax highlighting

---

### Infrastructure

**Containerization:** Docker + Docker Compose
- Service isolation
- Easy local development
- Production-like environment

**Reverse Proxy:** Nginx (in Docker)
- Serve frontend static files
- Proxy API requests
- Single entry point

---

## Component Details

### Scenario Definition Format

**File:** `packages/mock-scenarios/acl-regression.json`

```json
{
  "scenario_id": "acl-regression-001",
  "name": "ACL Regression Blocks Downstream Subnet",
  "description": "Engineer adds ACL deny rule that blocks downstream subnet",
  "duration_seconds": 240,
  "devices": [
    {
      "device_id": "edge-router-1",
      "hostname": "edge-router-1",
      "vendor": "cisco-ios",
      "role": "edge-router",
      "management_ip": "192.168.1.1",
      "states": [
        {
          "timestamp": 0,
          "config_path": "configs/edge-router-1-baseline.cfg",
          "cpu_usage": 20,
          "memory_usage": 45,
          "latency_ms": 7,
          "packet_loss_pct": 0,
          "interfaces": [
            {
              "name": "GigabitEthernet0/0",
              "admin_state": "up",
              "oper_state": "up",
              "rx_errors": 0,
              "tx_errors": 0,
              "description": "LAN-facing interface",
              "ip_address": "10.0.0.1/24"
            },
            {
              "name": "GigabitEthernet0/1",
              "admin_state": "up",
              "oper_state": "up",
              "rx_errors": 0,
              "tx_errors": 0,
              "description": "Uplink",
              "ip_address": "192.168.1.1/24"
            }
          ],
          "tags": ["healthy_baseline"]
        },
        {
          "timestamp": 60,
          "config_path": "configs/edge-router-1-faulty.cfg",
          "cpu_usage": 22,
          "memory_usage": 45,
          "latency_ms": 8,
          "packet_loss_pct": 0,
          "interfaces": [...],
          "tags": ["fault_introduced"]
        },
        {
          "timestamp": 120,
          "config_path": "configs/edge-router-1-faulty.cfg",
          "cpu_usage": 35,
          "memory_usage": 48,
          "latency_ms": 55,
          "packet_loss_pct": 10,
          "interfaces": [...],
          "tags": ["degradation_detected"]
        },
        ...
      ]
    },
    ...
  ]
}
```

---

### Database Schema Highlights

**See DATA_MODEL.md for full schema**

Key relationships:
- `devices` ← `snapshots` (one-to-many)
- `snapshots` ← `interface_snapshots` (one-to-many)
- `devices` ← `config_versions` (one-to-many)
- `config_versions` ← `config_diffs` (one-to-many)
- `devices` ← `events` (one-to-many)
- `incidents` ← `events` (many-to-many via incident_events)

---

## Integration Points

### Frontend ↔ API

**Protocol:** HTTP/REST  
**Data Format:** JSON  
**Authentication:** None (Phase 1)  
**CORS:** Enabled for `http://localhost:5173` (Vite dev server)

---

### API ↔ Database

**Connection:** PostgreSQL async driver (asyncpg)  
**ORM:** SQLAlchemy 2.0 async  
**Migrations:** Alembic  
**Connection Pooling:** SQLAlchemy engine pool

---

### API ↔ Git Repository

**Library:** GitPython  
**Repository Path:** `/data/config-repo/` (Docker volume)  
**Operations:** write, commit, log, diff  
**Concurrency:** Single-threaded Git operations (simple for Phase 1)

---

### Collector ↔ Scenario Engine

**Interface:** Direct Python imports (same process)  
**Data Format:** Python dataclasses  
**State Storage:** In-memory during scenario execution

---

## Deployment Architecture

### Docker Compose Services

```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: blackboxnet
      POSTGRES_USER: blackboxnet
      POSTGRES_PASSWORD: blackboxnet_dev
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: ./apps/api
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql://blackboxnet:blackboxnet_dev@db:5432/blackboxnet
      GIT_REPO_PATH: /data/config-repo
    volumes:
      - config_repo:/data/config-repo
      - ./apps/api:/app
    ports:
      - "8000:8000"
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  web:
    build: ./apps/web
    depends_on:
      - api
    ports:
      - "3000:80"
    environment:
      VITE_API_URL: http://localhost:8000

volumes:
  postgres_data:
  config_repo:
```

---

### Network Architecture

```
User Browser
    │
    ├─→ :3000 (Nginx serving React app)
    │   │
    │   └─→ :8000/api/* (proxied to API)
    │
API Service (:8000)
    │
    ├─→ PostgreSQL (:5432)
    └─→ Git Repo (volume mount)
```

---

## Future Extensibility

### Phase 2 Extensions (Real Device Polling)

**Components to Add:**
- SSH Collector (replaces ScenarioEngine)
- Command Executor (runs show commands)
- Vendor Parser Factory (selects parser by vendor)
- Scheduler (cron-like polling)

**Components to Modify:**
- CollectorService: switch from scenario to SSH
- EventEngine: add more sophisticated rules
- CorrelationEngine: add graph-based analysis

**Architecture Impact:**
- ScenarioEngine becomes development-only
- Collector interface remains the same
- Add vendor abstraction layer

---

### Phase 3 Extensions (Multi-Vendor)

**Components to Add:**
- Cisco IOS Parser
- Junos Parser
- Nokia SR OS Parser
- Vendor Profile Registry
- Canonical Model Mapper

**Data Model Changes:**
- Add `vendor_specific_data` JSONB column
- Add `canonical_model` JSONB column
- Add `parser_version` tracking

---

### Future Features

**Rollback Recommendations:**
- Identify "last known good config"
- Generate rollback commands
- Show config delta for rollback

**Advanced Correlation:**
- Graph-based causality analysis
- ML-based anomaly detection
- Cross-device dependency tracking

**Alerting:**
- Real-time event streaming
- Webhook notifications
- Email/Slack integration

**Multi-Tenancy:**
- User authentication
- Organization isolation
- RBAC for device access

---

## Design Decisions Log

| Decision | Rationale |
|----------|-----------|
| FastAPI over Flask | Async support, automatic OpenAPI, modern Python |
| PostgreSQL over MongoDB | Relational data, strong consistency, JSONB for flexibility |
| Git over custom versioning | Industry standard, familiar, powerful |
| shadcn/ui over Material-UI | No runtime overhead, full customization, modern |
| Docker Compose over k8s | Simpler for Phase 1, easy local development |
| React Context over Redux | Sufficient for Phase 1 scope, less boilerplate |
| GitPython over pygit2 | Pure Python, easier to install, good enough for Phase 1 |
| Manual step trigger over auto-play | Easier to debug, clearer for learning |

---

## Security Considerations (Phase 1)

**Current State:**
- No authentication (local development only)
- No encryption (HTTP only)
- No input validation beyond Pydantic
- No rate limiting

**Phase 2 Requirements:**
- Add JWT authentication
- Add HTTPS/TLS
- Add input sanitization
- Add rate limiting
- Add audit logging

---

**END OF ARCHITECTURE DOCUMENT**
