# BlackBoxNet - API Specification
## REST API Endpoints

**Version:** 1.0  
**Date:** 2024-11-15  
**Base URL:** `http://localhost:8000/api`

---

## Table of Contents

1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Common Response Formats](#common-response-formats)
4. [Devices API](#devices-api)
5. [Incidents API](#incidents-api)
6. [Config API](#config-api)
7. [Simulation API](#simulation-api)
8. [Error Handling](#error-handling)

---

## API Overview

### Design Principles

- **RESTful:** Resource-oriented URLs
- **JSON:** All request/response bodies in JSON
- **UTC Timestamps:** All timestamps in ISO 8601 format with timezone
- **Pagination:** Limit/offset for list endpoints
- **CORS:** Enabled for frontend development

### Base URL

```
Development: http://localhost:8000/api
Production: https://blackboxnet.example.com/api
```

### Content Type

```
Content-Type: application/json
Accept: application/json
```

---

## Authentication

**Phase 1:** No authentication required (local development only)

**Future Phases:** JWT bearer tokens

---

## Common Response Formats

### Success Response

```json
{
  "data": { /* resource or array */ },
  "meta": {
    "timestamp": "2024-11-15T10:23:45Z",
    "request_id": "uuid"
  }
}
```

### Paginated Response

```json
{
  "data": [ /* array of resources */ ],
  "meta": {
    "total": 100,
    "limit": 20,
    "offset": 0,
    "timestamp": "2024-11-15T10:23:45Z"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { /* optional additional context */ }
  },
  "meta": {
    "timestamp": "2024-11-15T10:23:45Z",
    "request_id": "uuid"
  }
}
```

---

## Devices API

### List Devices

```
GET /api/devices
```

**Description:** Get all network devices with latest health status

**Query Parameters:**
- `vendor` (optional) - Filter by vendor: `cisco-ios`, `junos`, `nokia-sros`
- `role` (optional) - Filter by role: `edge-router`, `dist-switch`, etc.
- `limit` (optional, default: 50) - Pagination limit
- `offset` (optional, default: 0) - Pagination offset

**Response:**
```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "hostname": "edge-router-1",
      "management_ip": "192.168.1.1",
      "vendor": "cisco-ios",
      "role": "edge-router",
      "latest_snapshot": {
        "timestamp": "2024-11-15T10:24:00Z",
        "cpu_usage": 72.5,
        "memory_usage": 48.3,
        "latency_ms": 55.2,
        "packet_loss_pct": 10.5,
        "health_status": "degraded"
      },
      "metadata": {
        "location": "datacenter-1",
        "rack": "R01"
      },
      "created_at": "2024-11-15T10:00:00Z"
    }
  ],
  "meta": {
    "total": 3,
    "limit": 50,
    "offset": 0,
    "timestamp": "2024-11-15T10:25:00Z"
  }
}
```

**Health Status Calculation:**
- `healthy`: packet_loss < 5%, latency < 50ms, cpu < 80%
- `degraded`: packet_loss 5-79%, latency 50-200ms, or cpu 80-95%
- `critical`: packet_loss >= 80%, latency > 200ms, or cpu > 95%

---

### Get Device by ID

```
GET /api/devices/{device_id}
```

**Description:** Get detailed device information

**Path Parameters:**
- `device_id` (UUID) - Device identifier

**Response:**
```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "hostname": "edge-router-1",
    "management_ip": "192.168.1.1",
    "vendor": "cisco-ios",
    "role": "edge-router",
    "latest_snapshot": {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "timestamp": "2024-11-15T10:24:00Z",
      "config_hash": "a1b2c3d4...",
      "cpu_usage": 72.5,
      "memory_usage": 48.3,
      "latency_ms": 55.2,
      "packet_loss_pct": 10.5,
      "interfaces": [
        {
          "name": "GigabitEthernet0/0",
          "admin_state": "up",
          "oper_state": "up",
          "rx_errors": 1250,
          "tx_errors": 890,
          "description": "LAN-facing interface",
          "ip_address": "10.0.0.1/24"
        }
      ]
    },
    "latest_config_version": {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "timestamp": "2024-11-15T10:23:45Z",
      "git_commit_hash": "abc123def456...",
      "config_path": "data/config-repo/edge-router-1/2024-11-15T10-23-45.cfg"
    },
    "metadata": {
      "location": "datacenter-1"
    },
    "created_at": "2024-11-15T10:00:00Z",
    "updated_at": "2024-11-15T10:23:45Z"
  }
}
```

---

### Get Device Health History

```
GET /api/devices/{device_id}/health
```

**Description:** Get time-series health metrics for a device

**Path Parameters:**
- `device_id` (UUID) - Device identifier

**Query Parameters:**
- `start_time` (ISO 8601) - Start of time range
- `end_time` (ISO 8601) - End of time range
- `limit` (optional, default: 100) - Max data points

**Response:**
```json
{
  "data": {
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "hostname": "edge-router-1",
    "time_series": [
      {
        "timestamp": "2024-11-15T10:22:00Z",
        "cpu_usage": 20.0,
        "memory_usage": 45.0,
        "latency_ms": 7.0,
        "packet_loss_pct": 0.0,
        "tags": ["healthy_baseline"]
      },
      {
        "timestamp": "2024-11-15T10:23:00Z",
        "cpu_usage": 22.0,
        "memory_usage": 45.0,
        "latency_ms": 8.0,
        "packet_loss_pct": 0.0,
        "tags": ["fault_introduced"]
      },
      {
        "timestamp": "2024-11-15T10:24:00Z",
        "cpu_usage": 35.0,
        "memory_usage": 48.0,
        "latency_ms": 55.0,
        "packet_loss_pct": 10.5,
        "tags": ["degradation_detected"]
      }
    ],
    "summary": {
      "data_points": 3,
      "start_time": "2024-11-15T10:22:00Z",
      "end_time": "2024-11-15T10:24:00Z"
    }
  }
}
```

---

### Get Device Snapshots

```
GET /api/devices/{device_id}/snapshots
```

**Description:** Get all snapshots for a device

**Path Parameters:**
- `device_id` (UUID) - Device identifier

**Query Parameters:**
- `start_time` (ISO 8601, optional)
- `end_time` (ISO 8601, optional)
- `tags` (comma-separated, optional) - Filter by tags
- `limit` (optional, default: 50)
- `offset` (optional, default: 0)

**Response:**
```json
{
  "data": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "device_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-11-15T10:23:45Z",
      "config_hash": "a1b2c3d4...",
      "cpu_usage": 22.0,
      "memory_usage": 45.0,
      "latency_ms": 8.0,
      "packet_loss_pct": 0.0,
      "snapshot_source": "simulation",
      "tags": ["fault_introduced"],
      "interfaces": [...]
    }
  ],
  "meta": {
    "total": 5,
    "limit": 50,
    "offset": 0
  }
}
```

---

## Incidents API

### List Incidents

```
GET /api/incidents
```

**Description:** Get all incidents

**Query Parameters:**
- `status` (optional) - Filter by status: `active`, `resolved`, `investigating`
- `start_time` (ISO 8601, optional) - Filter incidents starting after this time
- `limit` (optional, default: 50)
- `offset` (optional, default: 0)

**Response:**
```json
{
  "data": [
    {
      "id": "bb0e8400-e29b-41d4-a716-446655440006",
      "title": "ACL Regression Blocks Downstream Subnet",
      "start_time": "2024-11-15T10:24:00Z",
      "end_time": null,
      "status": "active",
      "affected_scope": "subnet 10.0.1.0/24, devices: access-switch-1, dist-switch-1",
      "root_device": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "hostname": "edge-router-1"
      },
      "summary": "Complete connectivity loss for subnet 10.0.1.0/24",
      "suspicion_summary": "ACL change on edge-router-1 at 10:23:45Z preceded latency spike and outage.",
      "event_count": 7,
      "affected_device_count": 3,
      "created_at": "2024-11-15T10:24:00Z"
    }
  ],
  "meta": {
    "total": 1,
    "limit": 50,
    "offset": 0
  }
}
```

---

### Get Incident by ID

```
GET /api/incidents/{incident_id}
```

**Description:** Get detailed incident information

**Path Parameters:**
- `incident_id` (UUID) - Incident identifier

**Response:**
```json
{
  "data": {
    "id": "bb0e8400-e29b-41d4-a716-446655440006",
    "title": "ACL Regression Blocks Downstream Subnet",
    "start_time": "2024-11-15T10:24:00Z",
    "end_time": null,
    "status": "active",
    "affected_scope": "subnet 10.0.1.0/24, devices: access-switch-1, dist-switch-1",
    "root_device": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "hostname": "edge-router-1",
      "vendor": "cisco-ios",
      "role": "edge-router"
    },
    "summary": "Complete connectivity loss for subnet 10.0.1.0/24 starting at 10:24:00Z",
    "suspicion_summary": "ACL change on edge-router-1 at 10:23:45Z preceded latency spike and outage. New deny rule blocks traffic from affected subnet 10.0.1.0/24.",
    "correlation": {
      "primary_suspect": {
        "event_id": "aa0e8400-e29b-41d4-a716-446655440005",
        "event_type": "CONFIG_CHANGE",
        "timestamp": "2024-11-15T10:23:45Z",
        "device_hostname": "edge-router-1"
      },
      "evidence": [
        "Config change occurred 15 seconds before first degradation",
        "Semantic diff shows ACL deny rule for 10.0.1.0/24",
        "All degradation events occurred downstream of config change"
      ],
      "suspicion_level": "high"
    },
    "affected_devices": [
      {
        "device_id": "550e8400-e29b-41d4-a716-446655440000",
        "hostname": "edge-router-1",
        "impact_level": "critical"
      },
      {
        "device_id": "550e8400-e29b-41d4-a716-446655440001",
        "hostname": "dist-switch-1",
        "impact_level": "high"
      },
      {
        "device_id": "550e8400-e29b-41d4-a716-446655440002",
        "hostname": "access-switch-1",
        "impact_level": "critical"
      }
    ],
    "event_summary": {
      "total": 7,
      "by_type": {
        "CONFIG_CHANGE": 1,
        "LATENCY_SPIKE": 2,
        "PACKET_LOSS_INCREASE": 1,
        "INTERFACE_DEGRADED": 1,
        "CPU_RISE": 1,
        "OUTAGE_STARTED": 1
      }
    },
    "created_at": "2024-11-15T10:24:00Z",
    "updated_at": "2024-11-15T10:24:05Z"
  }
}
```

---

### Get Incident Timeline

```
GET /api/incidents/{incident_id}/timeline
```

**Description:** Get chronological timeline of events for an incident

**Path Parameters:**
- `incident_id` (UUID) - Incident identifier

**Response:**
```json
{
  "data": {
    "incident_id": "bb0e8400-e29b-41d4-a716-446655440006",
    "events": [
      {
        "id": "aa0e8400-e29b-41d4-a716-446655440005",
        "device_id": "550e8400-e29b-41d4-a716-446655440000",
        "device_hostname": "edge-router-1",
        "timestamp": "2024-11-15T10:23:45Z",
        "event_type": "CONFIG_CHANGE",
        "severity": "INFO",
        "title": "Configuration changed",
        "description": "ACL modified on GigabitEthernet0/0",
        "config_diff": {
          "diff_id": "990e8400-e29b-41d4-a716-446655440004",
          "summary": "ACL 101 applied to interface Gi0/0, deny rule added for 10.0.1.0/24",
          "suspicion_level": "high"
        },
        "is_primary_cause": true,
        "relevance_score": 1.0
      },
      {
        "id": "ab0e8400-e29b-41d4-a716-446655440007",
        "device_id": "550e8400-e29b-41d4-a716-446655440001",
        "device_hostname": "dist-switch-1",
        "timestamp": "2024-11-15T10:24:00Z",
        "event_type": "LATENCY_SPIKE",
        "severity": "WARNING",
        "title": "Latency increased",
        "description": "Latency spiked to 65ms (baseline: 8ms)",
        "metadata": {
          "baseline_latency": 8.0,
          "current_latency": 65.0,
          "threshold": 50.0
        },
        "is_primary_cause": false,
        "relevance_score": 0.85
      },
      {
        "id": "ac0e8400-e29b-41d4-a716-446655440008",
        "device_id": "550e8400-e29b-41d4-a716-446655440002",
        "device_hostname": "access-switch-1",
        "timestamp": "2024-11-15T10:24:00Z",
        "event_type": "PACKET_LOSS_INCREASE",
        "severity": "WARNING",
        "title": "Packet loss detected",
        "description": "Packet loss increased to 35%",
        "metadata": {
          "baseline_packet_loss": 0.0,
          "current_packet_loss": 35.0
        },
        "is_primary_cause": false,
        "relevance_score": 0.90
      },
      {
        "id": "ad0e8400-e29b-41d4-a716-446655440009",
        "device_id": "550e8400-e29b-41d4-a716-446655440001",
        "device_hostname": "dist-switch-1",
        "timestamp": "2024-11-15T10:25:00Z",
        "event_type": "INTERFACE_DEGRADED",
        "severity": "ERROR",
        "title": "Interface errors increased",
        "description": "Gi0/1 rx_errors: 1250, tx_errors: 890",
        "metadata": {
          "interface": "GigabitEthernet0/1",
          "rx_errors": 1250,
          "tx_errors": 890
        },
        "is_primary_cause": false,
        "relevance_score": 0.75
      },
      {
        "id": "ae0e8400-e29b-41d4-a716-446655440010",
        "device_id": "550e8400-e29b-41d4-a716-446655440000",
        "device_hostname": "edge-router-1",
        "timestamp": "2024-11-15T10:25:00Z",
        "event_type": "CPU_RISE",
        "severity": "WARNING",
        "title": "CPU utilization increased",
        "description": "CPU at 72% (baseline: 20%)",
        "metadata": {
          "baseline_cpu": 20.0,
          "current_cpu": 72.0,
          "threshold": 70.0
        },
        "is_primary_cause": false,
        "relevance_score": 0.60
      },
      {
        "id": "af0e8400-e29b-41d4-a716-446655440011",
        "device_id": "550e8400-e29b-41d4-a716-446655440002",
        "device_hostname": "access-switch-1",
        "timestamp": "2024-11-15T10:26:00Z",
        "event_type": "OUTAGE_STARTED",
        "severity": "CRITICAL",
        "title": "Outage detected",
        "description": "Subnet 10.0.1.0/24 unreachable (100% packet loss)",
        "metadata": {
          "affected_subnet": "10.0.1.0/24",
          "packet_loss": 100.0
        },
        "is_primary_cause": false,
        "relevance_score": 1.0
      }
    ],
    "meta": {
      "total_events": 6,
      "time_span": {
        "start": "2024-11-15T10:23:45Z",
        "end": "2024-11-15T10:26:00Z",
        "duration_seconds": 135
      }
    }
  }
}
```

---

### Get Incident Correlation

```
GET /api/incidents/{incident_id}/correlation
```

**Description:** Get detailed correlation analysis for an incident

**Path Parameters:**
- `incident_id` (UUID) - Incident identifier

**Response:**
```json
{
  "data": {
    "incident_id": "bb0e8400-e29b-41d4-a716-446655440006",
    "suspicion_summary": "ACL change on edge-router-1 at 10:23:45Z preceded latency spike and outage. New deny rule blocks traffic from affected subnet 10.0.1.0/24.",
    "primary_suspect": {
      "event_id": "aa0e8400-e29b-41d4-a716-446655440005",
      "event_type": "CONFIG_CHANGE",
      "device_hostname": "edge-router-1",
      "timestamp": "2024-11-15T10:23:45Z",
      "reasoning": "First config change before degradation cascade"
    },
    "correlation_flags": [
      {
        "rule": "recent_config_change_before_degradation",
        "suspicion_level": "high",
        "description": "Config change occurred 15 seconds before first degradation event",
        "evidence": {
          "config_change_time": "2024-11-15T10:23:45Z",
          "first_degradation_time": "2024-11-15T10:24:00Z",
          "time_delta_seconds": 15
        }
      },
      {
        "rule": "acl_deny_affects_subnet",
        "suspicion_level": "high",
        "description": "New ACL deny rule matches affected subnet",
        "evidence": {
          "denied_subnet": "10.0.1.0/24",
          "affected_subnet": "10.0.1.0/24",
          "acl_name": "access-list 101",
          "deny_rule": "deny ip 10.0.1.0 0.0.0.255 any"
        }
      },
      {
        "rule": "time_ordered_primary_suspect",
        "suspicion_level": "high",
        "description": "Config change is chronologically first event",
        "evidence": {
          "config_change_time": "2024-11-15T10:23:45Z",
          "next_event_time": "2024-11-15T10:24:00Z"
        }
      }
    ],
    "timeline_analysis": {
      "config_changes_before_outage": 1,
      "degradation_events_after_config": 5,
      "time_to_outage_seconds": 135
    },
    "recommendation": "Review and rollback ACL change on edge-router-1. The deny rule for 10.0.1.0/24 should be removed or reordered after the permit statement."
  }
}
```

---

## Config API

### Get Config Versions

```
GET /api/devices/{device_id}/config/versions
```

**Description:** Get configuration version history for a device

**Path Parameters:**
- `device_id` (UUID) - Device identifier

**Query Parameters:**
- `limit` (optional, default: 50)
- `offset` (optional, default: 0)

**Response:**
```json
{
  "data": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "device_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-11-15T10:23:45Z",
      "git_commit_hash": "abc123def456...",
      "config_hash": "a1b2c3d4e5f6...",
      "config_path": "data/config-repo/edge-router-1/2024-11-15T10-23-45.cfg",
      "config_size_bytes": 2048
    },
    {
      "id": "880e8400-e29b-41d4-a716-446655440002",
      "device_id": "550e8400-e29b-41d4-a716-446655440000",
      "timestamp": "2024-11-15T10:22:00Z",
      "git_commit_hash": "def456abc789...",
      "config_hash": "b2c3d4e5f6a7...",
      "config_path": "data/config-repo/edge-router-1/2024-11-15T10-22-00.cfg",
      "config_size_bytes": 2045
    }
  ],
  "meta": {
    "total": 2,
    "limit": 50,
    "offset": 0
  }
}
```

---

### Get Config Diff

```
GET /api/devices/{device_id}/config/diff/{diff_id}
```

**Description:** Get configuration diff with semantic analysis

**Path Parameters:**
- `device_id` (UUID) - Device identifier
- `diff_id` (UUID) - Config diff identifier

**Response:**
```json
{
  "data": {
    "id": "990e8400-e29b-41d4-a716-446655440004",
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "device_hostname": "edge-router-1",
    "timestamp": "2024-11-15T10:23:45Z",
    "previous_version": {
      "id": "880e8400-e29b-41d4-a716-446655440002",
      "timestamp": "2024-11-15T10:22:00Z",
      "git_commit_hash": "def456abc789..."
    },
    "current_version": {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "timestamp": "2024-11-15T10:23:45Z",
      "git_commit_hash": "abc123def456..."
    },
    "diff_text": "--- a/config\n+++ b/config\n@@ -5,7 +5,8 @@\n  ip address 10.0.0.1 255.255.255.0\n- ip access-group 100 in\n+ ip access-group 101 in\n  no shutdown\n !\n-access-list 100 permit ip any any\n+access-list 101 deny ip 10.0.1.0 0.0.0.255 any\n+access-list 101 permit ip any any\n !",
    "lines_added": 3,
    "lines_removed": 1,
    "lines_changed": 4,
    "semantic_summary": [
      {
        "change_type": "INTERFACE_ACL_BINDING",
        "entity": "GigabitEthernet0/0",
        "action": "modified",
        "details": {
          "old_acl": "100",
          "new_acl": "101",
          "direction": "in"
        },
        "suspicion_level": "medium",
        "reason": "ACL binding changed on interface"
      },
      {
        "change_type": "ACL_MODIFIED",
        "entity": "access-list 101",
        "action": "added",
        "details": {
          "rule_added": "deny ip 10.0.1.0 0.0.0.255 any",
          "position": "before permit any",
          "affected_subnet": "10.0.1.0/24",
          "protocol": "ip",
          "action": "deny"
        },
        "suspicion_level": "high",
        "reason": "Deny rule added before permit affecting known subnet 10.0.1.0/24"
      }
    ],
    "suspicion_level": "high",
    "summary": "ACL 101 applied to Gi0/0 with new deny rule blocking 10.0.1.0/24"
  }
}
```

---

### Get Config Content

```
GET /api/devices/{device_id}/config/content
```

**Description:** Get raw configuration file content

**Path Parameters:**
- `device_id` (UUID) - Device identifier

**Query Parameters:**
- `version_id` (UUID, optional) - Specific version, defaults to latest
- `commit_hash` (string, optional) - Git commit hash

**Response:**
```json
{
  "data": {
    "device_id": "550e8400-e29b-41d4-a716-446655440000",
    "hostname": "edge-router-1",
    "version_id": "880e8400-e29b-41d4-a716-446655440003",
    "timestamp": "2024-11-15T10:23:45Z",
    "git_commit_hash": "abc123def456...",
    "content": "!\nhostname edge-router-1\n!\ninterface GigabitEthernet0/0\n description LAN-facing interface\n ip address 10.0.0.1 255.255.255.0\n ip access-group 101 in\n no shutdown\n!\ninterface GigabitEthernet0/1\n description Uplink\n ip address 192.168.1.1 255.255.255.0\n no shutdown\n!\naccess-list 101 deny ip 10.0.1.0 0.0.0.255 any\naccess-list 101 permit ip any any\n!\nend"
  }
}
```

---

## Simulation API

### Run Simulation Step

```
POST /api/simulation/run-step
```

**Description:** Advance simulation by one time step

**Request Body:**
```json
{
  "auto_advance": false  // If true, advance time; if false, just collect current state
}
```

**Response:**
```json
{
  "data": {
    "current_time": 120,
    "time_step": "T3",
    "devices_collected": 3,
    "snapshots_created": 3,
    "events_generated": [
      {
        "event_id": "ab0e8400-e29b-41d4-a716-446655440007",
        "event_type": "LATENCY_SPIKE",
        "device_hostname": "dist-switch-1"
      },
      {
        "event_id": "ac0e8400-e29b-41d4-a716-446655440008",
        "event_type": "PACKET_LOSS_INCREASE",
        "device_hostname": "access-switch-1"
      }
    ],
    "incidents_created": 0,
    "git_commits": 0
  },
  "meta": {
    "timestamp": "2024-11-15T10:24:00Z"
  }
}
```

---

### Reset Simulation

```
POST /api/simulation/reset
```

**Description:** Reset simulation to initial state

**Response:**
```json
{
  "data": {
    "status": "reset",
    "current_time": 0,
    "message": "Simulation reset to T1 (healthy baseline)"
  }
}
```

---

### Get Simulation Status

```
GET /api/simulation/status
```

**Description:** Get current simulation state

**Response:**
```json
{
  "data": {
    "current_time": 120,
    "current_step": "T3",
    "total_steps": 5,
    "scenario_name": "ACL Regression Blocks Downstream Subnet",
    "scenario_id": "acl-regression-001",
    "devices": [
      {
        "device_id": "550e8400-e29b-41d4-a716-446655440000",
        "hostname": "edge-router-1",
        "current_state": "degraded"
      },
      {
        "device_id": "550e8400-e29b-41d4-a716-446655440001",
        "hostname": "dist-switch-1",
        "current_state": "degraded"
      },
      {
        "device_id": "550e8400-e29b-41d4-a716-446655440002",
        "hostname": "access-switch-1",
        "current_state": "degraded"
      }
    ],
    "progress": {
      "percentage": 60,
      "next_step": "T4",
      "can_advance": true
    }
  }
}
```

---

## Error Handling

### HTTP Status Codes

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

### Error Response Example

```json
{
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "Device with ID 550e8400-e29b-41d4-a716-446655440099 not found",
    "details": {
      "device_id": "550e8400-e29b-41d4-a716-446655440099"
    }
  },
  "meta": {
    "timestamp": "2024-11-15T10:27:00Z",
    "request_id": "req_abc123"
  }
}
```

### Error Codes

- `DEVICE_NOT_FOUND` - Device does not exist
- `INCIDENT_NOT_FOUND` - Incident does not exist
- `CONFIG_DIFF_NOT_FOUND` - Config diff does not exist
- `INVALID_TIME_RANGE` - start_time must be before end_time
- `SIMULATION_ERROR` - Error in simulation engine
- `GIT_ERROR` - Error accessing Git repository
- `DATABASE_ERROR` - Database operation failed

---

**END OF API SPECIFICATION**
