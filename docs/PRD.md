# BlackBoxNet - Product Requirements Document
## Phase 1: Simulation-Driven MVP

**Version:** 1.0  
**Date:** 2024-11-15  
**Status:** Ready for Development  
**Target:** Cursor AI Implementation

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Product Identity](#product-identity)
3. [Target User](#target-user)
4. [Problem Statement](#problem-statement)
5. [Phase 1 Goals](#phase-1-goals)
6. [Scope Boundaries](#scope-boundaries)
7. [Network Topology](#network-topology)
8. [Outage Scenario](#outage-scenario)
9. [Success Criteria](#success-criteria)
10. [Non-Functional Requirements](#non-functional-requirements)

---

## Executive Summary

BlackBoxNet is a **network state replay platform** that records configuration snapshots, health metrics, and network events into a Git-backed timeline. It helps network engineers answer:

- **What changed before the outage?**
- **What config change likely caused the failure?**
- **What was the last known healthy state?**

### Phase 1 Objective
Build a web application that simulates a small network, records state over time, stores config versions in Git, and lets users replay one realistic outage scenario with rules-based correlation.

### Why Phase 1 Matters
Phase 1 must prove these product truths:
1. Time-indexed network state is useful for failure investigation
2. Git-backed config history adds investigative value
3. Timeline replay helps explain outages
4. Simple correlation can highlight suspicious changes

---

## Product Identity

### Product Name
**BlackBoxNet**

### Product Positioning
A network "flight recorder" and replay system—like an aircraft black box for network infrastructure.

### One-Line Description
BlackBoxNet is a time-indexed network state replay platform that reconstructs failure timelines so engineers can identify what changed before an outage.

### Phase 1 Identity
Phase 1 is a **simulation-driven MVP**—not a production polling system yet.

**It simulates:**
- Three network devices (router, distribution switch, access switch)
- One realistic outage scenario (ACL misconfiguration)
- Configuration changes over time
- Health degradation progression
- Event timeline generation
- Root cause correlation

---

## Target User

### Primary User
**Junior network engineer or networking lab user**

### User Profile
- Applies or studies Cisco-like or Juniper-like configurations
- Causes or encounters outages due to misconfiguration
- Does not yet have deep intuition for config blast radius
- Wants to understand cause-and-effect relationships
- Needs learning tools to build troubleshooting skills

### Core User Story
> *"My network broke after a config change. I want to see what changed, when it changed, and what likely caused the outage."*

### User Jobs-to-be-Done
1. **Investigate** – Understand what happened during an outage
2. **Learn** – Build intuition for how config changes affect network health
3. **Document** – Have a timeline to share with team or instructors
4. **Prevent** – Recognize patterns to avoid similar mistakes

---

## Problem Statement

### Current State Pain Points

**Fragmented Tooling:**
- Config backup tools show diffs but not network impact
- Monitoring tools show symptoms but not config context
- Logs are scattered across devices
- No unified timeline correlating config + health + events

**Knowledge Gap:**
- Junior engineers struggle to connect cause and effect
- No simple way to "replay" what happened
- Post-mortems are manual and time-consuming
- Learning from failures requires deep protocol knowledge

### What's Missing
There is no simple, replayable timeline that combines:
- Configuration history (what changed)
- Device health metrics (how it degraded)
- Interface state (where it failed)
- Outage progression (when it became critical)
- Correlation hints (why it likely happened)

**BlackBoxNet bridges this gap.**

---

## Phase 1 Goals

### Primary Goal
Build a web application that simulates a small network, records its state over time, stores config versions in Git, stores metrics/events in PostgreSQL, and lets users replay one realistic outage scenario.

### Success Metrics
A user can:
1. ✅ View three simulated network devices
2. ✅ View an incident summary with affected scope
3. ✅ Open a chronological timeline of events
4. ✅ See the exact config diff that occurred before degradation
5. ✅ See health and interface degradation after the config change
6. ✅ Read a rules-based suspicion statement linking the change to the outage
7. ✅ Understand the failure progression without networking expertise

### Product Validation Goals
Prove that:
- Timeline replay is intuitive and valuable
- Config diffs in context are more useful than standalone diffs
- Correlation hints reduce time-to-understanding
- The tool can be used for learning and training

---

## Scope Boundaries

### ✅ In Scope (Phase 1)

**Simulation & Data:**
- Three mocked devices (edge-router-1, dist-switch-1, access-switch-1)
- One pre-scripted scenario (ACL regression)
- Git-backed config snapshots
- Simulated metrics (CPU, memory, latency, packet loss)
- Simulated interface state changes
- Event generation from state deltas

**Core Features:**
- Incident timeline visualization
- Config diff viewer with line highlighting
- Device health dashboard
- Rules-based correlation engine
- Suspicion summary generation
- Replay UI (step-through timeline)

**Technical Components:**
- PostgreSQL database
- Git repository for configs
- FastAPI backend
- React frontend
- Docker Compose deployment

### ❌ Out of Scope (Phase 1)

**Not Implemented:**
- Real SSH polling of devices
- Real SNMP telemetry collection
- Live device discovery
- Multi-user authentication/authorization
- Cloud deployment architecture
- Full AI/ML root-cause engine
- Config remediation/push-back
- Production-scale topology support (>10 devices)
- Multi-scenario runtime switching
- Alert notification system
- Integration with existing NMS platforms

**Explicitly Deferred:**
- Juniper Junos parsing
- Nokia SR OS parsing
- OSPF/BGP neighbor state tracking
- Route-map semantic extraction
- NAT rule analysis
- Multi-vendor config normalization
- Advanced correlation (graph-based, ML)

---

## Network Topology

### Phase 1 Topology Overview
A realistic small enterprise/lab topology with three devices representing a simple routed network.

```
                    ┌─────────────────┐
                    │  edge-router-1  │
                    │   (Cisco-like)  │
                    │  192.168.1.1/24 │
                    │   10.0.0.1/24   │
                    └────────┬────────┘
                             │ Gi0/0 (LAN-facing)
                             │ ACL applied here
                             │
                    ┌────────▼────────┐
                    │ dist-switch-1   │
                    │  (L2/L3 switch) │
                    │  10.0.0.2/24    │
                    └────────┬────────┘
                             │
                             │
                    ┌────────▼────────┐
                    │ access-switch-1 │
                    │   (Access L2)   │
                    │ Downstream:     │
                    │  10.0.1.0/24    │
                    └─────────────────┘
```

### Device 1: edge-router-1

**Role:** L3 edge / policy enforcement point  
**Vendor Style:** Cisco IOS-like  
**Management IP:** 192.168.1.1  

**Primary Function:**
- Routes between connected segments
- Has inbound ACL applied on internal-facing interface (Gi0/0)
- Enforces access control policies

**Interfaces:**
- `GigabitEthernet0/0` – LAN-facing (10.0.0.1/24)
- `GigabitEthernet0/1` – Uplink/WAN (192.168.1.1/24)

**Key Config Elements:**
- Access-list definitions
- Interface ACL bindings
- IP addressing

### Device 2: dist-switch-1

**Role:** Distribution switch  
**Vendor Style:** Cisco-like  
**Management IP:** 10.0.0.2  

**Primary Function:**
- Uplink between router and access layer
- Forwards traffic between layers
- Exposes interface state and latency effects

**Interfaces:**
- `GigabitEthernet0/1` – Uplink to router
- `GigabitEthernet0/2` – Downlink to access switch

### Device 3: access-switch-1

**Role:** Access layer switch  
**Vendor Style:** Cisco-like  
**Management IP:** 10.0.1.1  

**Primary Function:**
- Represents the edge of the affected user subnet
- Serves downstream clients in 10.0.1.0/24

**Downstream Subnet:**
- 10.0.1.0/24 (simulated user segment)

### Logical Traffic Flow

**Normal State:**
Traffic from 10.0.1.0/24 → access-switch-1 → dist-switch-1 → edge-router-1 → external

**After Fault:**
Traffic from 10.0.1.0/24 is **denied** by ACL on edge-router-1 interface Gi0/0

---

## Outage Scenario

### Scenario Name
**ACL Regression Blocks Downstream Subnet**

### Scenario Overview
A network administrator modifies the ACL on the edge router's LAN-facing interface. The new ACL inadvertently includes a deny rule for the downstream subnet (10.0.1.0/24) **before** the broader permit rule. This causes immediate traffic disruption, progressive degradation, and eventual outage.

### Timeline: Five Time Steps

#### **T1 – Healthy Baseline** (t=0)
**State:**
- All devices healthy
- Router config permits all relevant traffic
- ACL 100 on Gi0/0: `permit ip any any`
- Latency nominal (<10ms)
- Interfaces up and clean
- Packet loss 0%
- No active incidents

**Snapshot Characteristics:**
- Tag: `healthy_baseline`
- CPU: 15-25% across devices
- Memory: 40-50% usage
- Interface errors: 0

---

#### **T2 – Config Change** (t=60s)
**Event:**
- Engineer modifies ACL on edge-router-1
- Old ACL 100 removed
- New ACL 101 applied to interface Gi0/0
- **New ACL logic:**
  ```
  access-list 101 deny ip 10.0.1.0 0.0.0.255 any
  access-list 101 permit ip any any
  ```

**System Response:**
- Config hash changes
- Git commit created: `config snapshot: 2024-11-15T10:23:45Z | changed: edge-router-1`
- Event emitted: `CONFIG_CHANGE`
  - Device: edge-router-1
  - Severity: INFO
  - Title: "Configuration changed"
  - Description: "ACL modified on GigabitEthernet0/0"

**State:**
- No immediate health impact (change just applied)
- Network still processing existing connections

**Snapshot Characteristics:**
- Tag: `fault_introduced`
- Metrics unchanged from T1

---

#### **T3 – Degradation Begins** (t=120s)
**State:**
- Traffic from 10.0.1.0/24 begins to fail
- New connection attempts blocked by ACL
- Retries and timeouts increase latency
- Packet loss begins to climb

**System Response:**
- Event emitted: `LATENCY_SPIKE`
  - Device: dist-switch-1
  - Severity: WARNING
  - Title: "Latency increased"
  - Description: "Latency spiked to 65ms (baseline: 8ms)"
- Event emitted: `PACKET_LOSS_INCREASE`
  - Device: access-switch-1
  - Severity: WARNING
  - Title: "Packet loss detected"
  - Description: "Packet loss increased to 35%"

**Metrics:**
- edge-router-1 latency: 55ms (was 7ms)
- dist-switch-1 latency: 65ms (was 8ms)
- access-switch-1 packet loss: 35% (was 0%)
- CPU slightly elevated on edge-router-1: 35%

**Snapshot Characteristics:**
- Tag: `degradation_detected`

---

#### **T4 – Interface/Resource Stress** (t=180s)
**State:**
- Sustained traffic blockage
- Interface error counters increase
- CPU rises as devices process failed connections
- Routing protocols may log warnings

**System Response:**
- Event emitted: `INTERFACE_DEGRADED`
  - Device: dist-switch-1
  - Severity: ERROR
  - Title: "Interface errors increased"
  - Description: "Gi0/1 rx_errors: 1250, tx_errors: 890"
- Event emitted: `CPU_RISE`
  - Device: edge-router-1
  - Severity: WARNING
  - Title: "CPU utilization increased"
  - Description: "CPU at 72% (baseline: 20%)"

**Metrics:**
- edge-router-1 CPU: 72% (was 20%)
- dist-switch-1 interface errors: rx=1250, tx=890
- Latency continues to climb: 85ms
- Packet loss: 60%

**Snapshot Characteristics:**
- Tag: `resource_stress`

---

#### **T5 – Outage** (t=240s)
**State:**
- Affected subnet (10.0.1.0/24) completely unreachable
- Packet loss reaches outage threshold (≥80%)
- Connectivity failed for all downstream clients

**System Response:**
- Event emitted: `OUTAGE_STARTED`
  - Device: access-switch-1
  - Severity: CRITICAL
  - Title: "Outage detected"
  - Description: "Subnet 10.0.1.0/24 unreachable (100% packet loss)"
- Incident created: "ACL Regression Blocks Downstream Subnet"
  - Status: ACTIVE
  - Affected scope: 10.0.1.0/24, access-switch-1, dist-switch-1
  - Root device: edge-router-1

**Metrics:**
- Packet loss: 100%
- Latency: unmeasurable (no response)
- Interface state: operationally degraded

**Snapshot Characteristics:**
- Tag: `outage_peak`

---

### Scenario Determinism

**Critical Requirement:** The scenario must be **100% deterministic and replayable**.

- Same input state → same output state
- Metrics follow predefined progression
- Events fire at exact time steps
- Git commits are predictable
- No randomness in Phase 1

---

## Configuration Semantics

### Vendor Syntax (Phase 1)

**Primary Simulated Syntax:** Cisco IOS/IOS-XE style

**Rationale:**
- Clear line-based running-config format
- Straightforward ACL semantics
- Easier line diffing
- Intuitive for networking labs and training

### Future Vendor Support (Phase 2+)
The architecture must anticipate:
- Cisco IOS/IOS-XE
- Juniper Junos
- Nokia SR OS

But Phase 1 implements **only Cisco-like syntax** for the active scenario.

---

### Baseline Router Config (Healthy)

```cisco
!
hostname edge-router-1
!
interface GigabitEthernet0/0
 description LAN-facing interface
 ip address 10.0.0.1 255.255.255.0
 ip access-group 100 in
 no shutdown
!
interface GigabitEthernet0/1
 description Uplink
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
access-list 100 permit ip any any
!
line vty 0 4
 login
!
end
```

---

### Fault-Inducing Router Config (After Change)

```cisco
!
hostname edge-router-1
!
interface GigabitEthernet0/0
 description LAN-facing interface
 ip address 10.0.0.1 255.255.255.0
 ip access-group 101 in
 no shutdown
!
interface GigabitEthernet0/1
 description Uplink
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
access-list 101 deny ip 10.0.1.0 0.0.0.255 any
access-list 101 permit ip any any
!
line vty 0 4
 login
!
end
```

---

### Semantic Meaning

**What Changed:**
1. Interface Gi0/0 ACL binding changed: `access-group 100` → `access-group 101`
2. New ACL 101 created with two rules:
   - `deny ip 10.0.1.0 0.0.0.255 any` ← **This blocks the downstream subnet**
   - `permit ip any any`

**Impact:**
- ACL processing is top-down, first-match wins
- Deny rule is evaluated before permit rule
- All traffic from 10.0.1.0/24 is dropped
- Downstream subnet becomes unreachable

**Why This Is Realistic:**
- Common mistake: adding deny rule without checking prefix order
- Typical scenario in lab environments and production errors
- Easy to overlook impact when focused on specific rule addition

---

### Phase 1 Config Intelligence Requirements

**Required Extraction:**
- Interface ACL binding (`ip access-group X in/out`)
- ACL number/name
- ACL rules (deny/permit, protocol, source subnet, dest subnet)
- Interface IP addresses
- Hostname

**Extraction Method:**
- Regex-based line parsing for Phase 1
- No full Cisco IOS parser required
- Scenario-specific semantic extraction only

**Not Required in Phase 1:**
- Full protocol stack parsing
- Route-map logic
- NAT statements
- QoS policies
- VRF extraction
- Complex firewall zone rules

---

## Vendor Abstraction Strategy

### Design Philosophy
Raw configs remain **vendor-native** (stored as-is in Git), but BlackBoxNet extracts selected semantics into a **canonical internal model** for correlation and display.

### Canonical Internal Model (Future)

**Entities to Abstract:**
- Hostname
- Interfaces (name, IPs, admin/oper state)
- ACL/filter attachment points
- ACL/filter rules (normalized)
- Static routes
- Routing neighbors (OSPF, BGP, etc.)
- VLAN membership
- Policy references

### Vendor Profiles (Future Architecture)

Each vendor profile defines:
- Config fetch command (e.g., `show running-config`)
- Health check commands (e.g., `show processes cpu`)
- Semantic extraction rules (regex patterns, parsers)
- Diff metadata hints
- Command output parsers

**Example Profiles:**
- `cisco-ios` profile
- `junos` profile
- `nokia-sros` profile

### Phase 1 Implementation Rule
**Phase 1 only needs:**
- One active Cisco-like scenario
- Passive documentation of Juniper/Nokia support in architecture
- No full multi-vendor parser implementation

**Future-Proofing:**
- Store configs as raw text (no vendor-specific binary formats)
- Design data model to accommodate vendor field
- Use abstraction layer between config storage and semantic extraction

---

## Success Criteria

### Functional Success Criteria

A demo user must be able to:

1. **View Device Dashboard**
   - See all three devices (edge-router-1, dist-switch-1, access-switch-1)
   - See current health status (healthy/degraded/critical)
   - See latest metric values (CPU, memory, latency, packet loss)
   - See device roles and management IPs

2. **View Incident List**
   - See the active incident: "ACL Regression Blocks Downstream Subnet"
   - See incident status, start time, affected scope
   - See suspicion summary preview

3. **Open Incident Timeline**
   - See chronological event list (T1 → T5)
   - See event types, severities, timestamps
   - See device attribution for each event
   - Navigate timeline with Previous/Next buttons

4. **Inspect Config Change Event**
   - Click the CONFIG_CHANGE event
   - See side-by-side config diff
   - See highlighted line changes
   - See semantic summary: "ACL 101 applied, deny rule added for 10.0.1.0/24"

5. **Understand Correlation**
   - See suspicion message linking config change to outage
   - See evidence: "Config changed 60s before latency spike"
   - See reasoning: "Deny rule affects downstream subnet 10.0.1.0/24"

6. **Verify Git Integration**
   - Confirm Git commit was created at T2
   - View commit in Git log
   - See commit message: `config snapshot: <timestamp> | changed: edge-router-1`

### Technical Success Criteria

1. **Database Integrity**
   - All snapshots stored correctly
   - Foreign key relationships valid
   - Timestamps in correct order
   - No orphaned records

2. **Git Repository**
   - Configs stored at correct paths
   - Commits only on config changes
   - Commit history clean and readable
   - Diffs work correctly

3. **API Functionality**
   - All endpoints return valid JSON
   - Response times <500ms for timeline queries
   - Proper error handling
   - CORS configured for frontend

4. **UI/UX**
   - Timeline renders without JavaScript errors
   - Config diff syntax highlighting works
   - Page loads in <2s
   - Mobile responsive (basic)

5. **Deployment**
   - Docker Compose brings up all services
   - Database migrations run automatically
   - Frontend served correctly
   - No manual configuration required

### Learning/Validation Success Criteria

1. **Can a non-expert understand what happened?**
   - Timeline tells a clear story
   - Suspicion message is actionable
   - Config diff is comprehensible

2. **Does the tool reduce time-to-understanding?**
   - Faster than manual log analysis
   - Faster than separate config diff + monitoring tools

3. **Is the correlation helpful?**
   - Suspicion accurately identifies the change
   - Evidence is relevant and clear

---

## Non-Functional Requirements

### Performance
- Timeline query: <500ms for 100 events
- Config diff generation: <200ms
- Dashboard load: <2s total page load
- Database queries: <100ms for device health

### Scalability (Phase 1 Limits)
- Max devices: 10
- Max snapshots per device: 1000
- Max events per incident: 500
- Max config file size: 100KB

### Reliability
- No data loss on container restart
- Database persistence via volumes
- Git repository persistence via volumes
- Graceful degradation if Git unavailable

### Security (Minimal for Phase 1)
- No authentication required (local development only)
- No sensitive data in configs
- No remote access enabled
- Docker network isolation

### Usability
- Timeline must be self-explanatory
- No networking expertise required to understand
- Config diffs use standard diff format
- Clear visual hierarchy in UI

### Maintainability
- Code must be well-documented
- Clear separation of concerns
- Reusable components
- Standard Python/JS conventions

### Compatibility
- Works on macOS, Linux, Windows (via Docker)
- Modern browsers (Chrome, Firefox, Safari, Edge)
- No browser plugins required
- Works offline after initial setup

---

## Open Questions for Development

1. **UI Component Library:** shadcn/ui + Tailwind or Material-UI?
2. **Time Progression:** Auto-advance simulation or manual step trigger?
3. **Config Diff Library:** React-diff-viewer or custom implementation?
4. **Timeline Visualization:** Vertical timeline or horizontal slider?
5. **Semantic Extraction:** Regex only or add pyparsing for future?

These will be answered in ARCHITECTURE.md and TECH_STACK.md.

---

## Document Change History

| Version | Date       | Author      | Changes                        |
|---------|------------|-------------|--------------------------------|
| 1.0     | 2024-11-15 | Claude      | Initial Cursor-ready PRD       |

---

## Related Documents

- `ARCHITECTURE.md` – System design and component architecture
- `DATA_MODEL.md` – Database schema and relationships
- `API_SPEC.md` – REST API endpoints and contracts
- `SEMANTIC_EXTRACTION.md` – Config parsing rules
- `SCENARIO_DEFINITION.md` – ACL scenario script
- `DEVELOPMENT_PHASES.md` – Build order and milestones
- `CURSOR_HANDOFF.md` – How to prompt Cursor for implementation

---

**END OF PRD**
