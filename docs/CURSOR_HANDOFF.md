# BlackBoxNet - Cursor Handoff Guide
## How to Implement with Cursor AI

**Version:** 1.0  
**Date:** 2024-11-15  
**Purpose:** Guide for using Cursor to implement BlackBoxNet Phase 1

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Cursor Setup](#cursor-setup)
3. [Implementation Strategy](#implementation-strategy)
4. [Component-by-Component Prompts](#component-by-component-prompts)
5. [Testing Prompts](#testing-prompts)
6. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Prerequisites

Before starting with Cursor:

1. **Read These Documents First:**
   - `PRD.md` - Understand product goals
   - `ARCHITECTURE.md` - Understand system design
   - `DATA_MODEL.md` - Understand database schema
   - `DEVELOPMENT_PHASES.md` - Understand build order

2. **Have These Tools Installed:**
   - Docker & Docker Compose
   - Python 3.11+
   - Node.js 18+
   - Git

3. **Create Project Directory:**
   ```bash
   mkdir blackboxnet
   cd blackboxnet
   ```

---

## Cursor Setup

### 1. Initialize Project Structure

**Cursor Prompt:**
```
Using the PROJECT_STRUCTURE.md document, create the complete directory 
structure for the BlackBoxNet project. Create all directories and 
placeholder files (.gitkeep, README.md) but don't implement code yet.

Also create:
- .gitignore with Python, Node, Docker, and IDE exclusions
- Root README.md with project overview
- docker-compose.yml skeleton (services defined, no implementation)
- .env.example files for api and web
```

**Expected Output:**
- Complete directory tree
- Empty placeholder files
- Basic configuration files

---

### 2. Add Documentation

**Cursor Prompt:**
```
Copy all documentation from my uploaded files into the docs/ directory:
- PRD.md
- ARCHITECTURE.md  
- DATA_MODEL.md
- API_SPEC.md
- SEMANTIC_EXTRACTION.md
- SCENARIO_DEFINITION.md
- DEVELOPMENT_PHASES.md
- PROJECT_STRUCTURE.md
- CURSOR_HANDOFF.md (this file)

Also create a docs/README.md that links to all documents with brief descriptions.
```

---

## Implementation Strategy

### Recommended Order

Follow DEVELOPMENT_PHASES.md exactly:

1. **Phase A: Foundation** - Database, models, Git
2. **Phase B: Scenario Engine** - Mock data provider
3. **Phase C: Collectors** - Data persistence
4. **Phase D: Event Detection** - Event engine
5. **Phase E: Diffs** - Config diffing and semantic extraction
6. **Phase F: Correlation** - Suspicion analysis
7. **Phase G: API** - REST endpoints
8. **Phase H-N: Frontend** - React UI

**Key Principle:** Each phase should be fully working before moving to the next.

---

## Component-by-Component Prompts

### Phase A: Foundation

#### Step A1: Docker Compose

**Cursor Prompt:**
```
Create a docker-compose.yml file for BlackBoxNet with these services:

1. PostgreSQL database:
   - Image: postgres:15
   - Environment: POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
   - Volume: postgres_data
   - Port: 5432

2. API service (skeleton for now):
   - Build from apps/api
   - Depends on: db
   - Environment: DATABASE_URL, GIT_REPO_PATH
   - Volumes: config_repo, ./apps/api:/app
   - Port: 8000

3. Web service (skeleton for now):
   - Build from apps/web  
   - Depends on: api
   - Port: 3000

Include named volumes for postgres_data and config_repo.

Also create apps/api/Dockerfile and apps/web/Dockerfile as skeletons.
```

---

#### Step A2: Database Models

**Cursor Prompt:**
```
Using DATA_MODEL.md as the specification, create SQLAlchemy models in apps/api/app/models/:

1. device.py - Device model with all columns from DATA_MODEL.md table definition
2. snapshot.py - Snapshot and InterfaceSnapshot models
3. config.py - ConfigVersion and ConfigDiff models  
4. event.py - Event model
5. incident.py - Incident, IncidentEvent, and IncidentAffectedDevice models

For each model:
- Use UUID primary keys with gen_random_uuid() default
- Include all constraints from DATA_MODEL.md (CHECK, UNIQUE, FK)
- Add relationships between models
- Use proper types (JSONB for metadata, ARRAY for tags, INET for IPs)
- Include created_at/updated_at timestamps where specified

Also create app/models/__init__.py that exports all models.
```

**Follow-up Verification Prompt:**
```
Review the models I just created against DATA_MODEL.md. Check:
1. All columns present with correct types
2. All constraints defined
3. All relationships properly configured
4. Indexes will be added in migrations (not in models)
```

---

#### Step A3: Alembic Setup

**Cursor Prompt:**
```
Set up Alembic for database migrations in apps/api:

1. Create alembic.ini with:
   - script_location = alembic
   - sqlalchemy.url from env var DATABASE_URL

2. Create alembic/env.py that:
   - Imports all models from app.models
   - Uses target_metadata = Base.metadata
   - Supports async database operations
   - Reads DATABASE_URL from environment

3. Create initial migration alembic/versions/001_initial_schema.py that:
   - Creates all tables from models
   - Creates all indexes from DATA_MODEL.md
   - Includes proper upgrade() and downgrade()

Reference DATA_MODEL.md for exact schema.
```

---

#### Step A4: Git Service Foundation

**Cursor Prompt:**
```
Create apps/api/app/services/config_git.py with a ConfigGitService class:

Initialize Git repository at GIT_REPO_PATH if it doesn't exist.

Methods:
- write_config(device_id, config_text, timestamp) -> str
  Write config to data/config-repo/{device_id}/{timestamp}.cfg
  Return the file path
  
- commit_changes(timestamp, changed_devices) -> str
  Git add all changed configs
  Create commit with message: "config snapshot: {timestamp} | changed: {devices}"
  Return commit hash
  
- get_config_at_commit(device_id, commit_hash) -> str
  Checkout commit and read config file
  Return config content

Use GitPython library (import git).
Handle errors gracefully (repository not initialized, file not found, etc.).
```

---

### Phase B: Scenario Engine

**Cursor Prompt:**
```
Create apps/api/app/core/scenario_engine.py with a ScenarioEngine class that:

1. Loads scenario from JSON file (packages/mock-scenarios/acl-regression.json)

2. Implements these methods:
   - load_scenario(scenario_path: str) -> None
     Parse JSON, validate structure, store in memory
   
   - get_device_state(device_id: str, timestamp: int) -> DeviceState
     Return device state at given timestamp
     If exact timestamp not found, return previous state
     
   - get_all_devices_state(timestamp: int) -> List[DeviceState]
     Return all device states at timestamp
     
   - advance_time() -> int
     Move to next time step, return new timestamp
     
   - get_current_time() -> int
     Return current timestamp
     
   - reset() -> None
     Reset to t=0

3. Define DeviceState dataclass with fields from SCENARIO_DEFINITION.md

4. Handle edge cases:
   - Requesting state before scenario start -> return None
   - Requesting state after scenario end -> return last state
   - Invalid device_id -> raise ValueError

The scenario JSON structure is defined in SCENARIO_DEFINITION.md.
```

**Test Prompt:**
```
Create tests/unit/test_scenario_engine.py that tests:
- Loading scenario from JSON
- Getting device state at each time step (T1-T5)
- Advancing time correctly
- Resetting scenario
- Edge cases (invalid device, out of range timestamp)

Use pytest and the scenario JSON from SCENARIO_DEFINITION.md.
```

---

### Phase C: Collectors & Snapshots

**Cursor Prompt:**
```
Create apps/api/app/services/collector.py with a CollectorService class:

Constructor takes:
- scenario_engine: ScenarioEngine
- db_session: AsyncSession
- config_git_service: ConfigGitService

Methods:
- async collect_all_devices() -> List[Snapshot]
  1. Get current timestamp from scenario_engine
  2. For each device, get device state
  3. Call snapshot_processor to persist
  4. If config changed, call config_git_service
  5. Return list of created snapshots

- async collect_device(device_id: str) -> Snapshot
  Same but for single device

The service should:
- Calculate config hash using hashlib.sha256
- Detect if config changed by comparing hashes
- Only create Git commit if at least one config changed
- Use batch operations where possible

Reference ARCHITECTURE.md for data flow.
```

**Related Prompt:**
```
Create apps/api/app/services/snapshot_processor.py with a SnapshotProcessor class:

Methods:
- async persist_snapshot(device_state: DeviceState, device_id: UUID) -> Snapshot
  1. Create Snapshot record from device_state
  2. Insert into database
  3. For each interface in device_state:
     Create InterfaceSnapshot record
  4. Return created Snapshot with interfaces loaded

- async get_previous_snapshot(device_id: UUID) -> Snapshot | None
  Get most recent snapshot for device before current time
  Return None if no previous snapshot

Handle database transactions properly.
Reference DATA_MODEL.md for exact schema.
```

---

### Phase D: Event Detection

**Cursor Prompt:**
```
Create apps/api/app/services/event_engine.py with an EventEngine class:

Implement event detection rules from SCENARIO_DEFINITION.md:

Methods:
- async detect_events(snapshot: Snapshot, previous: Snapshot | None) -> List[Event]
  Compare snapshots and emit events based on thresholds
  
  Rules to implement:
  1. CONFIG_CHANGE: config_hash differs
  2. LATENCY_SPIKE: latency_ms > 50 AND previous < 30
  3. PACKET_LOSS_INCREASE: packet_loss_pct > 20 AND previous < 10
  4. INTERFACE_DEGRADED: rx_errors increased by > 1000 OR oper_state == "degraded"
  5. CPU_RISE: cpu_usage > 70 AND previous < 40
  6. OUTAGE_STARTED: packet_loss_pct >= 80

- async emit_event(event_type, device_id, severity, title, description, metadata) -> Event
  Create Event record in database
  Link to related config_diff_id if provided
  Return created Event

Event types and severities defined in DATA_MODEL.md.
```

**Test Prompt:**
```
Create tests/unit/test_event_engine.py that verifies:
- CONFIG_CHANGE detected when hash changes
- LATENCY_SPIKE detected with correct threshold  
- PACKET_LOSS_INCREASE detected
- INTERFACE_DEGRADED detected
- CPU_RISE detected
- OUTAGE_STARTED detected
- No events when thresholds not exceeded

Create fixture snapshots with specific values to test each rule.
```

---

### Phase E: Config Diffs & Semantic Extraction

**Cursor Prompt:**
```
Create apps/api/app/services/diff_engine.py with a DiffEngine class:

Methods:
- async generate_diff(old_config: str, new_config: str, device_id: UUID) -> ConfigDiff
  1. Use difflib.unified_diff to create text diff
  2. Count lines added/removed/changed
  3. Call semantic extractor to analyze changes
  4. Determine overall suspicion level (max of semantic changes)
  5. Create ConfigDiff record with semantic_summary as JSONB
  6. Return ConfigDiff

- async get_diff(diff_id: UUID) -> ConfigDiff
  Retrieve diff by ID with all relations loaded

Reference SEMANTIC_EXTRACTION.md for diff format.
```

**Next Prompt:**
```
Create apps/api/app/core/semantic_extraction/cisco_ios.py with a CiscoIOSExtractor class:

Implement the exact code from SEMANTIC_EXTRACTION.md including:

1. PATTERNS dict with regex for:
   - acl_extended
   - interface_acl
   - interface_ip
   - hostname
   - interface_start
   - description

2. extract_changes(diff_text, old_config, new_config) -> List[SemanticChange]
   Parse configs and compare

3. _parse_config(config) -> dict
   Extract ACLs, interfaces, IPs, hostname

4. _compare_acls(old_data, new_data) -> List[SemanticChange]
   Find added/modified ACLs
   
5. _compare_interface_acls(old_data, new_data) -> List[SemanticChange]
   Find interface binding changes
   
6. _wildcard_to_cidr(ip, wildcard) -> str
   Convert Cisco wildcard to CIDR

Use the exact implementation from SEMANTIC_EXTRACTION.md.
```

---

### Phase F: Correlation Engine

**Cursor Prompt:**
```
Create apps/api/app/services/correlation_engine.py with a CorrelationEngine class:

Implement correlation rules from ARCHITECTURE.md:

Methods:
- async correlate_incident(incident_id: UUID) -> IncidentCorrelation
  1. Get all events for incident
  2. Apply correlation rules
  3. Generate suspicion summary
  4. Update incident with suspicion_summary
  5. Return correlation analysis

- async apply_rules(incident: Incident) -> List[CorrelationFlag]
  Apply these rules:
  
  Rule A: recent_config_change_before_degradation
  - Find CONFIG_CHANGE events
  - Find degradation events (LATENCY_SPIKE, PACKET_LOSS_INCREASE)
  - If config change within 5 minutes before degradation, flag it
  
  Rule B: acl_deny_affects_subnet  
  - Find CONFIG_CHANGE with semantic diff
  - Check if deny rule affects incident affected_scope subnet
  - If yes, high suspicion
  
  Rule C: time_ordered_primary_suspect
  - Find earliest CONFIG_CHANGE before other events
  - Mark as primary suspect

- generate_suspicion_summary(flags: List[CorrelationFlag]) -> str
  Create natural language summary like:
  "ACL change on edge-router-1 at {time} preceded latency spike and outage. 
   New deny rule blocks traffic from affected subnet {subnet}."

CorrelationFlag should be a dataclass with: rule, suspicion_level, evidence, description.
```

---

### Phase G: REST API

**Cursor Prompt:**
```
Create FastAPI application in apps/api/main.py:

1. Create FastAPI app with:
   - Title: "BlackBoxNet API"
   - Version: "1.0.0"
   - OpenAPI docs at /docs
   - CORS middleware allowing localhost:5173

2. Include routers from app/api/routes:
   - devices
   - incidents  
   - configs
   - simulation

3. Database session dependency in app/dependencies.py

4. Startup event to:
   - Run Alembic migrations
   - Initialize Git repository
   - Load scenario

Reference API_SPEC.md for endpoint structure.
```

**Next Prompt:**
```
Create apps/api/app/api/routes/devices.py with these endpoints from API_SPEC.md:

- GET /api/devices
  Query parameters: vendor, role, limit, offset
  Return list of devices with latest snapshot
  
- GET /api/devices/{device_id}
  Return device detail with latest snapshot, interfaces, config version
  
- GET /api/devices/{device_id}/health
  Query parameters: start_time, end_time, limit
  Return time-series of health metrics
  
- GET /api/devices/{device_id}/snapshots
  Query parameters: start_time, end_time, tags, limit, offset
  Return snapshots for device

Use Pydantic schemas for request/response validation.
Create schemas in app/schemas/device.py.
```

**Repeat for incidents, configs, simulation routes:**
```
Create apps/api/app/api/routes/incidents.py with endpoints from API_SPEC.md:
- GET /api/incidents
- GET /api/incidents/{incident_id}
- GET /api/incidents/{incident_id}/timeline
- GET /api/incidents/{incident_id}/correlation

Create corresponding schemas in app/schemas/incident.py.
```

---

### Phase H-N: Frontend

#### Phase H: Foundation

**Cursor Prompt:**
```
Initialize React + TypeScript + Vite project in apps/web:

1. Create package.json with dependencies from PROJECT_STRUCTURE.md
2. Create vite.config.ts with path aliases and API proxy
3. Create tsconfig.json with strict mode
4. Create tailwind.config.js with shadcn/ui setup
5. Create src/main.tsx with React Router
6. Create src/App.tsx with basic layout
7. Create route structure for:
   - / (Dashboard)
   - /devices
   - /devices/:id
   - /incidents
   - /incidents/:id

Use shadcn/ui for components (install with npx shadcn-ui@latest init).
```

---

#### API Client

**Cursor Prompt:**
```
Create apps/web/src/api/client.ts with axios instance:

- Base URL from VITE_API_URL env var
- Default timeout 10s
- Response interceptor for error handling

Then create API modules:
- src/api/devices.ts - getDevices(), getDevice(id), getDeviceHealth(id)
- src/api/incidents.ts - getIncidents(), getIncident(id), getTimeline(id)
- src/api/configs.ts - getConfigDiff(deviceId, diffId)
- src/api/simulation.ts - runStep(), reset(), getStatus()

Use TypeScript types from src/types/*.ts (create these from API_SPEC.md).
```

---

#### Components

**Cursor Prompt for Each Component:**
```
Create apps/web/src/components/devices/DeviceCard.tsx:

Props:
- device: Device (from src/types/device.ts)
- onClick?: () => void

Display:
- Device hostname
- Management IP
- Vendor (with icon if possible)
- Role badge
- Latest health metrics:
  - CPU usage (progress bar)
  - Memory usage (progress bar)
  - Latency (with unit)
  - Packet loss (with unit)
- Health status badge (healthy/degraded/critical)
  Color-coded: green/yellow/red

Use shadcn/ui components: Card, Badge, Progress.
Use Tailwind for styling.
Make it responsive.
```

**Repeat pattern for:**
- Timeline.tsx (vertical event timeline)
- EventCard.tsx (event in timeline)
- ConfigDiff.tsx (side-by-side diff viewer)
- CorrelationSummary.tsx (suspicion display)

---

## Testing Prompts

### Unit Tests

**Cursor Prompt:**
```
Create comprehensive unit tests for {module_name}:

Test file: tests/unit/test_{module_name}.py

For each method in the class:
1. Test happy path
2. Test edge cases
3. Test error conditions
4. Mock external dependencies

Use pytest fixtures for common setup.
Aim for 80%+ code coverage.
Add docstrings explaining what each test validates.
```

---

### Integration Tests

**Cursor Prompt:**
```
Create integration test for full scenario execution:

Test file: tests/integration/test_scenario_execution.py

Test flow:
1. Setup: Clean database, initialize scenario
2. Run T1: Collect snapshots, verify healthy state
3. Run T2: Config change, verify Git commit, verify CONFIG_CHANGE event
4. Run T3: Verify LATENCY_SPIKE and PACKET_LOSS_INCREASE events
5. Run T4: Verify INTERFACE_DEGRADED and CPU_RISE events
6. Run T5: Verify OUTAGE_STARTED event, incident created
7. Verify correlation: Check suspicion_summary, primary suspect
8. Teardown: Clean database

Use actual database (test database from docker-compose).
Use pytest-asyncio for async tests.
```

---

## Troubleshooting

### Common Issues

#### Database Connection Fails

**Cursor Prompt:**
```
Debug database connection issue. Check:
1. Is PostgreSQL container running? (docker ps)
2. Are environment variables correct?
3. Is DATABASE_URL format correct?
4. Can I connect with psql? (docker exec -it blackboxnet-db-1 psql...)
5. Are migrations up to date? (alembic current)

Show me how to verify each step and fix the issue.
```

---

#### Git Repository Errors

**Cursor Prompt:**
```
Debug Git repository issue. The config_git_service is failing with: {error_message}

Check:
1. Is /data/config-repo volume mounted correctly?
2. Does the directory have write permissions?
3. Is Git initialized? (git status in container)
4. Can I manually create a commit?

Provide fixes for each potential issue.
```

---

#### Frontend API Calls Failing

**Cursor Prompt:**
```
Frontend cannot reach API. In browser console I see: {error_message}

Debug:
1. Is API running? (docker logs blackboxnet-api-1)
2. Is proxy configured correctly in vite.config.ts?
3. Are CORS headers set in FastAPI?
4. Is API URL correct in frontend .env?
5. Can I curl the endpoint successfully?

Show me how to fix this step by step.
```

---

## Best Practices for Cursor

### 1. Iterative Development

Don't ask Cursor to build everything at once. Instead:

```
✅ Good: "Create the Device model in app/models/device.py with all fields from DATA_MODEL.md"
❌ Bad: "Build the entire backend"
```

---

### 2. Reference Documentation

Always point Cursor to relevant docs:

```
✅ Good: "Using SEMANTIC_EXTRACTION.md, implement the CiscoIOSExtractor class"
❌ Bad: "Make a config parser"
```

---

### 3. Ask for Review

After Cursor generates code:

```
"Review the EventEngine class against the event detection rules in 
SCENARIO_DEFINITION.md. Are all thresholds correct?"
```

---

### 4. Test Incrementally

After each component:

```
"Create tests for the code you just generated. Test all methods and edge cases."
```

---

### 5. Fix Issues Specifically

When debugging:

```
✅ Good: "The LATENCY_SPIKE event is not triggering at T3. The threshold check 
        in EventEngine.detect_events() might be wrong. Review against 
        SCENARIO_DEFINITION.md and fix."
❌ Bad: "Events don't work. Fix it."
```

---

## Final Integration Prompt

When all phases are complete:

**Cursor Prompt:**
```
Let's do an end-to-end test of BlackBoxNet:

1. Start services: docker-compose up -d
2. Verify database migrations ran
3. Verify Git repository initialized
4. Load frontend at http://localhost:3000
5. Walk through scenario:
   - T1: View healthy dashboard
   - T2: Trigger config change, verify Git commit
   - T3: See degradation events appear
   - T4: See resource stress
   - T5: See outage and incident created
6. Open incident detail
7. View timeline
8. Inspect config diff
9. Read correlation summary
10. Reset simulation
11. Verify everything returns to T1

Document any issues found and create a checklist for demo readiness.
```

---

## Handoff Complete

You now have a complete guide for implementing BlackBoxNet with Cursor AI. 

**Next Steps:**
1. Read all documentation in /docs
2. Follow DEVELOPMENT_PHASES.md for build order
3. Use prompts from this guide for each component
4. Test incrementally after each phase
5. Integrate at the end

**Good luck building BlackBoxNet! 🚀**

---

**END OF CURSOR HANDOFF GUIDE**
