# BlackBoxNet - Data Model
## Database Schema and Relationships

**Version:** 1.0  
**Date:** 2024-11-15  
**Database:** PostgreSQL 15+

---

## Table of Contents

1. [Schema Overview](#schema-overview)
2. [Table Definitions](#table-definitions)
3. [Relationships](#relationships)
4. [Indexes](#indexes)
5. [Migration Strategy](#migration-strategy)
6. [Sample Data](#sample-data)
7. [Query Patterns](#query-patterns)

---

## Schema Overview

### Entity-Relationship Diagram

```
devices (1) ──< (N) snapshots
                     │
                     └──< interface_snapshots

devices (1) ──< (N) config_versions
                     │
                     └──< config_diffs

devices (1) ──< (N) events

incidents (1) ──< (N) incident_events >──< (N) events

incidents (N) >──< (N) devices (via incident_affected_devices)
```

---

### Design Principles

1. **Temporal Data**: All entities have timestamps for timeline reconstruction
2. **Immutability**: Events and snapshots are never updated, only inserted
3. **JSONB Flexibility**: Metadata stored in JSONB for extensibility
4. **Foreign Keys**: Strong referential integrity
5. **Cascading Deletes**: Configured where appropriate to maintain consistency

---

## Table Definitions

### 1. devices

**Purpose:** Master registry of network devices

```sql
CREATE TABLE devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hostname VARCHAR(255) NOT NULL UNIQUE,
    management_ip INET NOT NULL,
    vendor VARCHAR(50) NOT NULL,  -- cisco-ios, junos, nokia-sros
    role VARCHAR(50) NOT NULL,    -- edge-router, dist-switch, access-switch, etc.
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_vendor CHECK (vendor IN ('cisco-ios', 'junos', 'nokia-sros', 'other')),
    CONSTRAINT valid_role CHECK (role IN ('edge-router', 'core-router', 'dist-switch', 
                                           'access-switch', 'firewall', 'load-balancer', 'other'))
);

CREATE INDEX idx_devices_hostname ON devices(hostname);
CREATE INDEX idx_devices_vendor ON devices(vendor);
CREATE INDEX idx_devices_role ON devices(role);
```

**Example:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "hostname": "edge-router-1",
  "management_ip": "192.168.1.1",
  "vendor": "cisco-ios",
  "role": "edge-router",
  "metadata": {
    "location": "datacenter-1",
    "rack": "R01",
    "serial_number": "FOC12345678"
  }
}
```

---

### 2. snapshots

**Purpose:** Point-in-time device state captures

```sql
CREATE TABLE snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    config_hash VARCHAR(64) NOT NULL,  -- SHA256 of config content
    cpu_usage DECIMAL(5,2),            -- 0.00 to 100.00
    memory_usage DECIMAL(5,2),         -- 0.00 to 100.00
    latency_ms DECIMAL(10,2),          -- milliseconds
    packet_loss_pct DECIMAL(5,2),      -- 0.00 to 100.00
    snapshot_source VARCHAR(50) NOT NULL DEFAULT 'simulation',  -- simulation, ssh, snmp, api
    metadata JSONB DEFAULT '{}'::jsonb,
    tags TEXT[] DEFAULT ARRAY[]::TEXT[],  -- healthy_baseline, fault_introduced, etc.
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_cpu CHECK (cpu_usage >= 0 AND cpu_usage <= 100),
    CONSTRAINT valid_memory CHECK (memory_usage >= 0 AND memory_usage <= 100),
    CONSTRAINT valid_latency CHECK (latency_ms >= 0),
    CONSTRAINT valid_packet_loss CHECK (packet_loss_pct >= 0 AND packet_loss_pct <= 100),
    CONSTRAINT valid_snapshot_source CHECK (snapshot_source IN ('simulation', 'ssh', 'snmp', 'api'))
);

CREATE INDEX idx_snapshots_device_timestamp ON snapshots(device_id, timestamp DESC);
CREATE INDEX idx_snapshots_timestamp ON snapshots(timestamp DESC);
CREATE INDEX idx_snapshots_config_hash ON snapshots(config_hash);
CREATE INDEX idx_snapshots_tags ON snapshots USING GIN(tags);
```

**Example:**
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-11-15T10:23:45Z",
  "config_hash": "a1b2c3d4e5f6...",
  "cpu_usage": 22.50,
  "memory_usage": 45.30,
  "latency_ms": 8.20,
  "packet_loss_pct": 0.00,
  "snapshot_source": "simulation",
  "tags": ["fault_introduced"],
  "metadata": {
    "collection_duration_ms": 150,
    "polling_method": "scenario_engine"
  }
}
```

---

### 3. interface_snapshots

**Purpose:** Interface-level state at each snapshot time

```sql
CREATE TABLE interface_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    snapshot_id UUID NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
    interface_name VARCHAR(100) NOT NULL,
    admin_state VARCHAR(20) NOT NULL,  -- up, down
    oper_state VARCHAR(20) NOT NULL,   -- up, down, degraded
    rx_errors BIGINT DEFAULT 0,
    tx_errors BIGINT DEFAULT 0,
    rx_bytes BIGINT DEFAULT 0,
    tx_bytes BIGINT DEFAULT 0,
    description TEXT,
    ip_address INET,
    speed_mbps INTEGER,
    duplex VARCHAR(20),  -- full, half, auto
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_admin_state CHECK (admin_state IN ('up', 'down')),
    CONSTRAINT valid_oper_state CHECK (oper_state IN ('up', 'down', 'degraded'))
);

CREATE INDEX idx_interface_snapshots_snapshot ON interface_snapshots(snapshot_id);
CREATE INDEX idx_interface_snapshots_name ON interface_snapshots(interface_name);
CREATE INDEX idx_interface_snapshots_composite ON interface_snapshots(snapshot_id, interface_name);
```

**Example:**
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "snapshot_id": "660e8400-e29b-41d4-a716-446655440001",
  "interface_name": "GigabitEthernet0/0",
  "admin_state": "up",
  "oper_state": "up",
  "rx_errors": 0,
  "tx_errors": 0,
  "description": "LAN-facing interface",
  "ip_address": "10.0.0.1",
  "speed_mbps": 1000,
  "duplex": "full"
}
```

---

### 4. config_versions

**Purpose:** Track configuration versions and Git linkage

```sql
CREATE TABLE config_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    git_commit_hash VARCHAR(40) NOT NULL,  -- Git SHA-1
    config_hash VARCHAR(64) NOT NULL,      -- SHA256 of config content
    config_path TEXT NOT NULL,             -- Path in Git repo
    config_size_bytes INTEGER,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_config_versions_device_timestamp ON config_versions(device_id, timestamp DESC);
CREATE INDEX idx_config_versions_commit_hash ON config_versions(git_commit_hash);
CREATE INDEX idx_config_versions_config_hash ON config_versions(config_hash);
CREATE UNIQUE INDEX idx_config_versions_device_commit ON config_versions(device_id, git_commit_hash);
```

**Example:**
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-11-15T10:23:45Z",
  "git_commit_hash": "abc123def456...",
  "config_hash": "a1b2c3d4e5f6...",
  "config_path": "data/config-repo/edge-router-1/2024-11-15T10-23-45.cfg",
  "config_size_bytes": 2048
}
```

---

### 5. config_diffs

**Purpose:** Store diff metadata and semantic summaries

```sql
CREATE TABLE config_diffs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    previous_config_version_id UUID REFERENCES config_versions(id) ON DELETE SET NULL,
    current_config_version_id UUID NOT NULL REFERENCES config_versions(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    diff_text TEXT NOT NULL,  -- Unified diff format
    lines_added INTEGER DEFAULT 0,
    lines_removed INTEGER DEFAULT 0,
    lines_changed INTEGER DEFAULT 0,
    semantic_summary JSONB DEFAULT '[]'::jsonb,  -- Array of SemanticChange objects
    suspicion_level VARCHAR(20) DEFAULT 'low',   -- low, medium, high, critical
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_suspicion_level CHECK (suspicion_level IN ('low', 'medium', 'high', 'critical'))
);

CREATE INDEX idx_config_diffs_device ON config_diffs(device_id);
CREATE INDEX idx_config_diffs_timestamp ON config_diffs(timestamp DESC);
CREATE INDEX idx_config_diffs_current_version ON config_diffs(current_config_version_id);
CREATE INDEX idx_config_diffs_suspicion ON config_diffs(suspicion_level);
```

**Example:**
```json
{
  "id": "990e8400-e29b-41d4-a716-446655440004",
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "previous_config_version_id": "880e8400-e29b-41d4-a716-446655440002",
  "current_config_version_id": "880e8400-e29b-41d4-a716-446655440003",
  "timestamp": "2024-11-15T10:23:45Z",
  "diff_text": "--- a/config\n+++ b/config\n...",
  "lines_added": 3,
  "lines_removed": 1,
  "lines_changed": 4,
  "semantic_summary": [
    {
      "change_type": "ACL_MODIFIED",
      "entity": "access-list 101",
      "action": "added",
      "details": {
        "rule_added": "deny ip 10.0.1.0 0.0.0.255 any",
        "position": "before permit any",
        "affected_subnet": "10.0.1.0/24"
      },
      "suspicion_level": "high",
      "reason": "Deny rule added before permit affecting known subnet"
    }
  ],
  "suspicion_level": "high"
}
```

---

### 6. events

**Purpose:** Timeline events for state changes and detections

```sql
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    related_config_diff_id UUID REFERENCES config_diffs(id) ON DELETE SET NULL,
    related_snapshot_id UUID REFERENCES snapshots(id) ON DELETE SET NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT valid_event_type CHECK (event_type IN (
        'CONFIG_CHANGE', 'LATENCY_SPIKE', 'PACKET_LOSS_INCREASE',
        'INTERFACE_DEGRADED', 'INTERFACE_ERRORS', 'CPU_RISE',
        'MEMORY_RISE', 'OUTAGE_STARTED', 'OUTAGE_ENDED',
        'CORRELATION_FLAG', 'DEVICE_UNREACHABLE', 'DEVICE_RECOVERED'
    )),
    CONSTRAINT valid_severity CHECK (severity IN ('INFO', 'WARNING', 'ERROR', 'CRITICAL'))
);

CREATE INDEX idx_events_device_timestamp ON events(device_id, timestamp DESC);
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_events_event_type ON events(event_type);
CREATE INDEX idx_events_severity ON events(severity);
CREATE INDEX idx_events_config_diff ON events(related_config_diff_id) WHERE related_config_diff_id IS NOT NULL;
```

**Example:**
```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440005",
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-11-15T10:23:45Z",
  "event_type": "CONFIG_CHANGE",
  "severity": "INFO",
  "title": "Configuration changed",
  "description": "ACL modified on GigabitEthernet0/0",
  "related_config_diff_id": "990e8400-e29b-41d4-a716-446655440004",
  "metadata": {
    "change_summary": "ACL 101 applied to interface Gi0/0",
    "user": "admin",
    "source": "scenario_engine"
  }
}
```

---

### 7. incidents

**Purpose:** Grouped outage/failure cases with correlation

```sql
CREATE TABLE incidents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    affected_scope TEXT,  -- Human-readable: "subnet 10.0.1.0/24, devices: access-switch-1"
    root_device_id UUID REFERENCES devices(id) ON DELETE SET NULL,
    summary TEXT,
    suspicion_summary TEXT,  -- Generated by correlation engine
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    
    CONSTRAINT valid_status CHECK (status IN ('active', 'resolved', 'investigating', 'acknowledged'))
);

CREATE INDEX idx_incidents_start_time ON incidents(start_time DESC);
CREATE INDEX idx_incidents_status ON incidents(status);
CREATE INDEX idx_incidents_root_device ON incidents(root_device_id);
```

**Example:**
```json
{
  "id": "bb0e8400-e29b-41d4-a716-446655440006",
  "title": "ACL Regression Blocks Downstream Subnet",
  "start_time": "2024-11-15T10:24:00Z",
  "end_time": null,
  "status": "active",
  "affected_scope": "subnet 10.0.1.0/24, devices: access-switch-1, dist-switch-1",
  "root_device_id": "550e8400-e29b-41d4-a716-446655440000",
  "summary": "Complete connectivity loss for subnet 10.0.1.0/24 starting at 10:24:00Z",
  "suspicion_summary": "ACL change on edge-router-1 at 10:23:45Z preceded latency spike and outage. New deny rule blocks traffic from affected subnet 10.0.1.0/24."
}
```

---

### 8. incident_events

**Purpose:** Many-to-many relationship between incidents and events

```sql
CREATE TABLE incident_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    relevance_score DECIMAL(3,2) DEFAULT 1.0,  -- 0.00 to 1.00
    is_primary_cause BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_incident_event UNIQUE(incident_id, event_id),
    CONSTRAINT valid_relevance CHECK (relevance_score >= 0 AND relevance_score <= 1)
);

CREATE INDEX idx_incident_events_incident ON incident_events(incident_id);
CREATE INDEX idx_incident_events_event ON incident_events(event_id);
CREATE INDEX idx_incident_events_primary_cause ON incident_events(is_primary_cause) 
    WHERE is_primary_cause = TRUE;
```

---

### 9. incident_affected_devices

**Purpose:** Many-to-many relationship between incidents and affected devices

```sql
CREATE TABLE incident_affected_devices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    incident_id UUID NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    device_id UUID NOT NULL REFERENCES devices(id) ON DELETE CASCADE,
    impact_level VARCHAR(20) NOT NULL,  -- low, medium, high, critical
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    CONSTRAINT unique_incident_device UNIQUE(incident_id, device_id),
    CONSTRAINT valid_impact_level CHECK (impact_level IN ('low', 'medium', 'high', 'critical'))
);

CREATE INDEX idx_incident_affected_devices_incident ON incident_affected_devices(incident_id);
CREATE INDEX idx_incident_affected_devices_device ON incident_affected_devices(device_id);
```

---

## Relationships

### Primary Relationships

```
devices (1) ──< (N) snapshots
  - One device has many snapshots over time
  - Cascade delete: Remove device → remove all snapshots

snapshots (1) ──< (N) interface_snapshots
  - One snapshot contains many interface states
  - Cascade delete: Remove snapshot → remove interface snapshots

devices (1) ──< (N) config_versions
  - One device has many config versions over time
  - Cascade delete: Remove device → remove all config versions

config_versions (1) ──< (N) config_diffs (as current_config_version_id)
  - One config version can be the "current" in many diffs
  - Cascade delete: Remove config version → remove diffs

config_versions (1) ──< (N) config_diffs (as previous_config_version_id)
  - One config version can be the "previous" in many diffs
  - Set null on delete: Remove old version → set previous to NULL

devices (1) ──< (N) events
  - One device generates many events
  - Cascade delete: Remove device → remove events

incidents (N) >──< (N) events (via incident_events)
  - Many-to-many: One incident can have many events
  - One event can belong to multiple incidents (rare but possible)

incidents (N) >──< (N) devices (via incident_affected_devices)
  - Many-to-many: One incident can affect many devices
  - One device can be involved in many incidents over time
```

---

## Indexes

### Performance-Critical Indexes

**Timeline Queries:**
```sql
CREATE INDEX idx_events_timestamp ON events(timestamp DESC);
CREATE INDEX idx_snapshots_timestamp ON snapshots(timestamp DESC);
```

**Device Lookup:**
```sql
CREATE INDEX idx_snapshots_device_timestamp ON snapshots(device_id, timestamp DESC);
CREATE INDEX idx_events_device_timestamp ON events(device_id, timestamp DESC);
```

**Config Correlation:**
```sql
CREATE INDEX idx_events_config_diff ON events(related_config_diff_id) 
    WHERE related_config_diff_id IS NOT NULL;
```

**Incident Investigation:**
```sql
CREATE INDEX idx_incident_events_incident ON incident_events(incident_id);
CREATE INDEX idx_incident_affected_devices_incident ON incident_affected_devices(incident_id);
```

---

## Migration Strategy

### Alembic Setup

**Directory Structure:**
```
apps/api/
├── alembic/
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_indexes.py
│   │   └── ...
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
└── models/
    ├── device.py
    ├── snapshot.py
    ├── config.py
    ├── event.py
    └── incident.py
```

---

### Migration 001: Initial Schema

```python
"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-11-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create devices table
    op.create_table(
        'devices',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('hostname', sa.String(255), nullable=False, unique=True),
        sa.Column('management_ip', postgresql.INET(), nullable=False),
        sa.Column('vendor', sa.String(50), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, 
                  server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=False, 
                  server_default=sa.text('NOW()')),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.CheckConstraint("vendor IN ('cisco-ios', 'junos', 'nokia-sros', 'other')", 
                          name='valid_vendor'),
        sa.CheckConstraint("role IN ('edge-router', 'core-router', 'dist-switch', 'access-switch', 'firewall', 'load-balancer', 'other')", 
                          name='valid_role')
    )
    
    # Create snapshots table
    op.create_table(
        'snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, 
                  server_default=sa.text('gen_random_uuid()')),
        sa.Column('device_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('config_hash', sa.String(64), nullable=False),
        sa.Column('cpu_usage', sa.DECIMAL(5, 2)),
        sa.Column('memory_usage', sa.DECIMAL(5, 2)),
        sa.Column('latency_ms', sa.DECIMAL(10, 2)),
        sa.Column('packet_loss_pct', sa.DECIMAL(5, 2)),
        sa.Column('snapshot_source', sa.String(50), nullable=False, 
                  server_default='simulation'),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('tags', postgresql.ARRAY(sa.Text), server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, 
                  server_default=sa.text('NOW()')),
        sa.ForeignKeyConstraint(['device_id'], ['devices.id'], ondelete='CASCADE'),
        sa.CheckConstraint('cpu_usage >= 0 AND cpu_usage <= 100', name='valid_cpu'),
        sa.CheckConstraint('memory_usage >= 0 AND memory_usage <= 100', name='valid_memory'),
        sa.CheckConstraint('latency_ms >= 0', name='valid_latency'),
        sa.CheckConstraint('packet_loss_pct >= 0 AND packet_loss_pct <= 100', name='valid_packet_loss')
    )
    
    # Continue for all tables...
    # (Full migration code would include all 9 tables)

def downgrade():
    op.drop_table('incident_affected_devices')
    op.drop_table('incident_events')
    op.drop_table('incidents')
    op.drop_table('events')
    op.drop_table('config_diffs')
    op.drop_table('config_versions')
    op.drop_table('interface_snapshots')
    op.drop_table('snapshots')
    op.drop_table('devices')
```

---

## Sample Data

### Seed Data for Development

```sql
-- Insert devices
INSERT INTO devices (id, hostname, management_ip, vendor, role, metadata) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'edge-router-1', '192.168.1.1', 'cisco-ios', 'edge-router', 
 '{"location": "datacenter-1", "rack": "R01"}'::jsonb),
('550e8400-e29b-41d4-a716-446655440001', 'dist-switch-1', '10.0.0.2', 'cisco-ios', 'dist-switch',
 '{"location": "datacenter-1", "rack": "R02"}'::jsonb),
('550e8400-e29b-41d4-a716-446655440002', 'access-switch-1', '10.0.1.1', 'cisco-ios', 'access-switch',
 '{"location": "datacenter-1", "rack": "R03"}'::jsonb);

-- Sample snapshot (T1 - healthy baseline)
INSERT INTO snapshots (device_id, timestamp, config_hash, cpu_usage, memory_usage, 
                      latency_ms, packet_loss_pct, tags) VALUES
('550e8400-e29b-41d4-a716-446655440000', '2024-11-15 10:22:00+00', 
 'abc123...', 20.0, 45.0, 7.0, 0.0, ARRAY['healthy_baseline']);
```

---

## Query Patterns

### Common Query Examples

**Get latest snapshot for all devices:**
```sql
SELECT DISTINCT ON (device_id)
    s.*,
    d.hostname,
    d.vendor
FROM snapshots s
JOIN devices d ON d.id = s.device_id
ORDER BY device_id, timestamp DESC;
```

**Get timeline for an incident:**
```sql
SELECT 
    e.*,
    d.hostname,
    cd.diff_text,
    cd.semantic_summary
FROM incident_events ie
JOIN events e ON e.id = ie.event_id
JOIN devices d ON d.id = e.device_id
LEFT JOIN config_diffs cd ON cd.id = e.related_config_diff_id
WHERE ie.incident_id = $1
ORDER BY e.timestamp ASC;
```

**Find config changes before degradation:**
```sql
WITH degradation_time AS (
    SELECT MIN(timestamp) as first_degradation
    FROM events
    WHERE event_type IN ('LATENCY_SPIKE', 'PACKET_LOSS_INCREASE')
      AND device_id = $1
)
SELECT 
    e.*,
    cd.*
FROM events e
JOIN config_diffs cd ON cd.id = e.related_config_diff_id
CROSS JOIN degradation_time dt
WHERE e.event_type = 'CONFIG_CHANGE'
  AND e.timestamp < dt.first_degradation
  AND e.timestamp > dt.first_degradation - INTERVAL '5 minutes'
ORDER BY e.timestamp DESC;
```

**Get device health over time:**
```sql
SELECT 
    timestamp,
    cpu_usage,
    memory_usage,
    latency_ms,
    packet_loss_pct
FROM snapshots
WHERE device_id = $1
ORDER BY timestamp ASC;
```

---

**END OF DATA MODEL DOCUMENT**
