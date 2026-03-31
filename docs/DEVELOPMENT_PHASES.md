# BlackBoxNet - Development Phases
## Build Order and Implementation Roadmap

**Version:** 1.0  
**Date:** 2024-11-15  
**Target:** Phase 1 MVP

---

## Table of Contents

1. [Development Overview](#development-overview)
2. [Phase Breakdown](#phase-breakdown)
3. [Sprint Plan](#sprint-plan)
4. [Testing Strategy](#testing-strategy)
5. [Definition of Done](#definition-of-done)

---

## Development Overview

### Build Philosophy

**Bottom-Up + Iterative:**
1. Build data layer first (database, models)
2. Build core business logic (collectors, engines)
3. Build API layer
4. Build UI layer
5. Integrate and test end-to-end

**Vertical Slices:**
- Each phase delivers a working subset
- Can demo progress at each milestone
- Reduces integration risk

---

## Phase Breakdown

### Phase A: Foundation (Week 1)

**Goal:** Database, basic models, Git integration working

**Deliverables:**
- [ ] PostgreSQL database running in Docker
- [ ] Alembic migrations configured
- [ ] SQLAlchemy models for all tables
- [ ] Git repository initialized
- [ ] Scenario JSON file loaded
- [ ] Basic project structure established

**Success Criteria:**
- Can create database tables via migration
- Can insert/query devices from database
- Can write/commit configs to Git
- Scenario JSON parses correctly

---

### Phase B: Scenario Engine (Week 1-2)

**Goal:** Mock scenario engine provides device states

**Deliverables:**
- [ ] ScenarioEngine class loads JSON
- [ ] Can query device state at any timestamp
- [ ] Can advance time step-by-step
- [ ] Config files generated from scenario
- [ ] Interface snapshots generated

**Success Criteria:**
- `get_device_state("edge-router-1", t=0)` returns correct data
- Advancing time updates internal state
- Config content matches scenario specification
- All 5 time steps (T1-T5) work correctly

---

### Phase C: Collectors & Snapshots (Week 2)

**Goal:** Collect scenario data and persist to database

**Deliverables:**
- [ ] CollectorService queries scenario engine
- [ ] SnapshotProcessor persists snapshots
- [ ] Interface snapshots persisted
- [ ] Config hash calculation working
- [ ] ConfigGitService writes configs to Git
- [ ] Git commits created on config changes

**Success Criteria:**
- Running collection creates snapshot records
- Interface snapshots linked correctly
- Git commit created at T2 (config change)
- Config diff can be retrieved from Git

---

### Phase D: Event Detection (Week 2-3)

**Goal:** Detect events from snapshot deltas

**Deliverables:**
- [ ] EventEngine compares snapshots
- [ ] All event types detected correctly:
  - [ ] CONFIG_CHANGE
  - [ ] LATENCY_SPIKE
  - [ ] PACKET_LOSS_INCREASE
  - [ ] INTERFACE_DEGRADED
  - [ ] CPU_RISE
  - [ ] OUTAGE_STARTED
- [ ] Events persisted to database
- [ ] Event metadata populated

**Success Criteria:**
- T2 generates CONFIG_CHANGE event
- T3 generates LATENCY_SPIKE and PACKET_LOSS_INCREASE
- T4 generates INTERFACE_DEGRADED and CPU_RISE
- T5 generates OUTAGE_STARTED event
- All events have correct severity

---

### Phase E: Config Diffs & Semantic Extraction (Week 3)

**Goal:** Generate diffs with semantic analysis

**Deliverables:**
- [ ] DiffEngine generates text diffs
- [ ] CiscoIOSExtractor parses configs
- [ ] Semantic changes extracted:
  - [ ] ACL_MODIFIED
  - [ ] INTERFACE_ACL_BINDING
- [ ] Suspicion levels assigned
- [ ] ConfigDiff records created in database

**Success Criteria:**
- T2 config diff shows ACL changes
- Semantic summary identifies deny rule
- Suspicion level is "high"
- Diff linked to CONFIG_CHANGE event

---

### Phase F: Correlation Engine (Week 3-4)

**Goal:** Analyze timeline and generate suspicion

**Deliverables:**
- [ ] CorrelationEngine applies rules
- [ ] Rule A: recent_config_change_before_degradation
- [ ] Rule B: acl_deny_affects_subnet
- [ ] Rule C: time_ordered_primary_suspect
- [ ] Suspicion summary generation
- [ ] Incident created at T5
- [ ] Incident linked to all events

**Success Criteria:**
- T5 creates incident record
- Incident has all 3 correlation flags
- Suspicion summary matches expected text
- Primary suspect correctly identified as CONFIG_CHANGE
- All timeline events linked to incident

---

### Phase G: REST API (Week 4)

**Goal:** Expose data via REST API

**Deliverables:**
- [ ] FastAPI application structure
- [ ] All endpoints implemented:
  - [ ] GET /api/devices
  - [ ] GET /api/devices/{id}
  - [ ] GET /api/devices/{id}/health
  - [ ] GET /api/incidents
  - [ ] GET /api/incidents/{id}
  - [ ] GET /api/incidents/{id}/timeline
  - [ ] GET /api/incidents/{id}/correlation
  - [ ] GET /api/devices/{id}/config/diff/{diff_id}
  - [ ] POST /api/simulation/run-step
  - [ ] POST /api/simulation/reset
- [ ] CORS configured
- [ ] Error handling
- [ ] OpenAPI docs generated

**Success Criteria:**
- All endpoints return correct data
- Response format matches API spec
- OpenAPI docs accessible at /docs
- Can trigger simulation via API

---

### Phase H: Frontend Foundation (Week 4-5)

**Goal:** React app with basic routing and layout

**Deliverables:**
- [ ] Vite + React project setup
- [ ] React Router configured
- [ ] shadcn/ui components installed
- [ ] Basic layout with navigation
- [ ] Routes created:
  - [ ] / (Dashboard)
  - [ ] /devices
  - [ ] /incidents
  - [ ] /incidents/:id
- [ ] API client (axios) configured
- [ ] Basic state management (Context)

**Success Criteria:**
- App loads without errors
- Navigation between pages works
- Can fetch data from API
- Tailwind CSS working

---

### Phase I: Device Dashboard (Week 5)

**Goal:** Display device health

**Deliverables:**
- [ ] DeviceCard component
- [ ] Device list page
- [ ] Device detail page
- [ ] Health status visualization
- [ ] Metric display (CPU, memory, latency, packet loss)
- [ ] Interface list display

**Success Criteria:**
- Dashboard shows 3 devices
- Health status color-coded (healthy/degraded/critical)
- Clicking device navigates to detail page
- Metrics display correctly

---

### Phase J: Incident Timeline (Week 5-6)

**Goal:** Visualize incident timeline

**Deliverables:**
- [ ] Timeline component (vertical)
- [ ] Event card component
- [ ] Incident list page
- [ ] Incident detail page
- [ ] Event detail drawer/panel
- [ ] Timeline step navigation (prev/next)
- [ ] Event severity indicators

**Success Criteria:**
- Incident detail shows timeline
- Events sorted chronologically
- Can click event to see details
- Timeline visually clear and readable
- Prev/Next navigation works

---

### Phase K: Config Diff Viewer (Week 6)

**Goal:** Display config diffs with semantic analysis

**Deliverables:**
- [ ] ConfigDiff component (side-by-side or unified)
- [ ] Syntax highlighting for Cisco configs
- [ ] Semantic summary display
- [ ] Suspicion level indicator
- [ ] Link from CONFIG_CHANGE event to diff
- [ ] Diff navigation (previous/next config version)

**Success Criteria:**
- Clicking CONFIG_CHANGE event opens diff
- Diff shows before/after configs
- Changed lines highlighted
- Semantic summary shows ACL changes
- Suspicion level "high" displayed prominently

---

### Phase L: Correlation Display (Week 6)

**Goal:** Show correlation analysis and suspicion

**Deliverables:**
- [ ] CorrelationSummary component
- [ ] Evidence list display
- [ ] Primary suspect highlighting
- [ ] Recommendation display
- [ ] Correlation flags visualization

**Success Criteria:**
- Incident detail shows suspicion summary
- Evidence clearly presented
- Primary suspect event highlighted in timeline
- Recommendation actionable

---

### Phase M: Simulation Controls (Week 6-7)

**Goal:** Control simulation advancement

**Deliverables:**
- [ ] Simulation status display
- [ ] Run step button
- [ ] Reset button
- [ ] Progress indicator
- [ ] Auto-refresh on step
- [ ] Loading states

**Success Criteria:**
- Clicking "Run Step" advances simulation
- Dashboard updates after step
- Reset button returns to T1
- Progress bar shows current position

---

### Phase N: Polish & Documentation (Week 7)

**Goal:** Final polish and documentation

**Deliverables:**
- [ ] Error handling improved
- [ ] Loading states polished
- [ ] Empty states designed
- [ ] README.md with setup instructions
- [ ] Docker Compose documentation
- [ ] User guide / walkthrough
- [ ] Code comments cleaned up
- [ ] Demo script prepared

**Success Criteria:**
- No console errors
- Graceful error handling
- Professional UI polish
- Complete setup documentation
- Can run demo from scratch in <5 minutes

---

## Sprint Plan

### Sprint 1: Foundation & Core Logic (Weeks 1-3)

**Phases:** A, B, C, D, E

**Goal:** Backend fully functional

**Demo:** 
- Show database tables
- Show Git commits
- Show event records
- Query timeline from database

---

### Sprint 2: Correlation & API (Weeks 3-4)

**Phases:** F, G

**Goal:** API exposes complete data

**Demo:**
- Show API endpoints in Swagger
- Query timeline via API
- Show correlation analysis

---

### Sprint 3: Frontend Core (Weeks 4-6)

**Phases:** H, I, J, K

**Goal:** UI shows timeline and diffs

**Demo:**
- Navigate to incident
- View timeline
- Inspect config diff
- See correlation

---

### Sprint 4: Integration & Polish (Weeks 6-7)

**Phases:** L, M, N

**Goal:** End-to-end demo ready

**Demo:**
- Full walkthrough: healthy → config change → degradation → outage
- Show suspicion summary
- Show recommendation

---

## Testing Strategy

### Unit Tests

**Coverage Target:** 80%

**Priority Areas:**
- Event detection logic
- Semantic extraction
- Correlation rules
- API endpoint logic

**Tools:** pytest, pytest-cov

---

### Integration Tests

**Key Scenarios:**
- Full scenario execution (T1 → T5)
- Database persistence
- Git commit creation
- API endpoint integration

---

### End-to-End Tests

**User Flows:**
1. View healthy state
2. Trigger config change
3. View degradation events
4. View outage incident
5. Inspect config diff
6. Read correlation summary

**Tools:** Playwright or Cypress (optional for Phase 1)

---

### Manual Testing Checklist

- [ ] Can start from fresh database
- [ ] Run step 1 (T1) → see healthy state
- [ ] Run step 2 (T2) → see config change event
- [ ] View config diff → see ACL changes
- [ ] Run step 3 (T3) → see degradation events
- [ ] Run step 4 (T4) → see resource stress
- [ ] Run step 5 (T5) → see outage and incident
- [ ] View incident timeline → see all events
- [ ] View correlation → see suspicion summary
- [ ] Reset simulation → back to T1
- [ ] Repeat scenario → deterministic results

---

## Definition of Done

### Feature Complete
- [ ] All acceptance criteria met
- [ ] Unit tests written and passing
- [ ] Integration tests passing
- [ ] Code reviewed (if team)
- [ ] Documentation updated
- [ ] No console errors or warnings

### Phase Complete
- [ ] All features in phase complete
- [ ] Demo prepared and rehearsed
- [ ] Known issues documented
- [ ] Handoff notes written for next phase

### MVP Complete
- [ ] All 14 phases (A-N) complete
- [ ] Full scenario walkthrough works
- [ ] Docker Compose deployment works
- [ ] README has complete setup instructions
- [ ] Demo script ready
- [ ] Product validates PRD goals

---

## Risk Mitigation

### Technical Risks

**Risk:** Semantic extraction too complex
**Mitigation:** Keep Phase 1 scope narrow (ACL only), regex-based

**Risk:** Git integration issues
**Mitigation:** Use GitPython (battle-tested), test early

**Risk:** Frontend timeline performance
**Mitigation:** Keep event count low (<100), use React.memo

**Risk:** Database migration failures
**Mitigation:** Test migrations in clean database, use rollback

---

### Schedule Risks

**Risk:** Underestimated effort
**Mitigation:** Cut Phase N polish if needed, MVP still functional

**Risk:** Blocked on dependencies
**Mitigation:** Build in vertical slices, each phase independently demoable

---

## Success Metrics

### Technical Metrics
- [ ] All API tests passing
- [ ] 80% code coverage
- [ ] <2s page load time
- [ ] <500ms API response time
- [ ] Zero console errors

### Product Metrics
- [ ] Can demo scenario in <5 minutes
- [ ] Non-engineer can understand timeline
- [ ] Suspicion summary actionable
- [ ] Setup from scratch in <10 minutes

---

**END OF DEVELOPMENT PHASES DOCUMENT**
