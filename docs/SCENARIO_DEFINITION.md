# BlackBoxNet - Scenario Definition
## ACL Regression Scenario Specification

**Version:** 1.0  
**Date:** 2024-11-15  
**Scenario ID:** `acl-regression-001`

---

## Scenario Overview

**Name:** ACL Regression Blocks Downstream Subnet

**Description:** A network administrator modifies the ACL on the edge router's LAN-facing interface. The new ACL inadvertently includes a deny rule for the downstream subnet (10.0.1.0/24) before the broader permit rule, causing immediate traffic disruption and eventual outage.

**Duration:** 240 seconds (4 minutes)

**Time Steps:** 5 (T1, T2, T3, T4, T5)

**Affected Subnet:** 10.0.1.0/24

---

## Scenario Timeline

### T1 - Healthy Baseline (t=0s)

**State:** All systems normal

**Tags:** `healthy_baseline`

#### edge-router-1
```yaml
timestamp: 0
config_path: "configs/edge-router-1-baseline.cfg"
cpu_usage: 20.0
memory_usage: 45.0
latency_ms: 7.0
packet_loss_pct: 0.0
interfaces:
  - name: "GigabitEthernet0/0"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 0
    tx_errors: 0
    description: "LAN-facing interface"
    ip_address: "10.0.0.1/24"
  - name: "GigabitEthernet0/1"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 0
    tx_errors: 0
    description: "Uplink"
    ip_address: "192.168.1.1/24"
```

#### dist-switch-1
```yaml
timestamp: 0
config_path: "configs/dist-switch-1-baseline.cfg"
cpu_usage: 18.0
memory_usage: 42.0
latency_ms: 8.0
packet_loss_pct: 0.0
interfaces:
  - name: "GigabitEthernet0/1"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 0
    tx_errors: 0
    description: "Uplink to router"
    ip_address: "10.0.0.2/24"
  - name: "GigabitEthernet0/2"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 0
    tx_errors: 0
    description: "Downlink to access"
```

#### access-switch-1
```yaml
timestamp: 0
config_path: "configs/access-switch-1-baseline.cfg"
cpu_usage: 15.0
memory_usage: 40.0
latency_ms: 9.0
packet_loss_pct: 0.0
interfaces:
  - name: "GigabitEthernet0/1"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 0
    tx_errors: 0
    description: "Uplink to distribution"
  - name: "GigabitEthernet0/24"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 0
    tx_errors: 0
    description: "User port - 10.0.1.0/24 subnet"
```

---

### T2 - Config Change (t=60s)

**State:** Engineer modifies ACL on edge-router-1

**Tags:** `fault_introduced`

**Events to Generate:**
- `CONFIG_CHANGE` on edge-router-1

#### edge-router-1
```yaml
timestamp: 60
config_path: "configs/edge-router-1-faulty.cfg"  # ← CONFIG CHANGED
config_hash: "new_hash_different_from_baseline"
cpu_usage: 22.0  # slight increase
memory_usage: 45.0
latency_ms: 8.0
packet_loss_pct: 0.0
interfaces:
  - name: "GigabitEthernet0/0"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 0
    tx_errors: 0
    description: "LAN-facing interface"
    ip_address: "10.0.0.1/24"
  - name: "GigabitEthernet0/1"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 0
    tx_errors: 0
    description: "Uplink"
    ip_address: "192.168.1.1/24"
```

**Git Commit:**
```
Commit: abc123def456...
Author: scenario-engine
Date: 2024-11-15T10:23:45Z
Message: config snapshot: 2024-11-15T10:23:45Z | changed: edge-router-1

Files changed:
  data/config-repo/edge-router-1/2024-11-15T10-23-45.cfg
```

**Config Diff:**
```diff
--- a/edge-router-1-baseline.cfg
+++ b/edge-router-1-faulty.cfg
@@ -5,7 +5,8 @@
  ip address 10.0.0.1 255.255.255.0
- ip access-group 100 in
+ ip access-group 101 in
  no shutdown
 !
-access-list 100 permit ip any any
+access-list 101 deny ip 10.0.1.0 0.0.0.255 any
+access-list 101 permit ip any any
 !
```

#### dist-switch-1
```yaml
timestamp: 60
config_path: "configs/dist-switch-1-baseline.cfg"  # unchanged
cpu_usage: 18.0
memory_usage: 42.0
latency_ms: 8.0
packet_loss_pct: 0.0
interfaces: [same as T1]
```

#### access-switch-1
```yaml
timestamp: 60
config_path: "configs/access-switch-1-baseline.cfg"  # unchanged
cpu_usage: 15.0
memory_usage: 40.0
latency_ms: 9.0
packet_loss_pct: 0.0
interfaces: [same as T1]
```

---

### T3 - Degradation Begins (t=120s)

**State:** Traffic from 10.0.1.0/24 starts failing

**Tags:** `degradation_detected`

**Events to Generate:**
- `LATENCY_SPIKE` on dist-switch-1
- `PACKET_LOSS_INCREASE` on access-switch-1

#### edge-router-1
```yaml
timestamp: 120
config_path: "configs/edge-router-1-faulty.cfg"  # unchanged
cpu_usage: 35.0  # ↑ increased due to rejected packets
memory_usage: 48.0
latency_ms: 55.0  # ↑ increased
packet_loss_pct: 10.0  # ↑ started losing packets
interfaces:
  - name: "GigabitEthernet0/0"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 150  # ↑ errors appearing
    tx_errors: 80
    description: "LAN-facing interface"
    ip_address: "10.0.0.1/24"
  - name: "GigabitEthernet0/1"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 0
    tx_errors: 0
    description: "Uplink"
    ip_address: "192.168.1.1/24"
```

#### dist-switch-1
```yaml
timestamp: 120
config_path: "configs/dist-switch-1-baseline.cfg"
cpu_usage: 28.0  # ↑ increased
memory_usage: 44.0
latency_ms: 65.0  # ↑ SPIKE - triggers LATENCY_SPIKE event
packet_loss_pct: 15.0  # ↑ increased
interfaces:
  - name: "GigabitEthernet0/1"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 200  # ↑ errors
    tx_errors: 150
    description: "Uplink to router"
    ip_address: "10.0.0.2/24"
  - name: "GigabitEthernet0/2"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 180
    tx_errors: 120
    description: "Downlink to access"
```

#### access-switch-1
```yaml
timestamp: 120
config_path: "configs/access-switch-1-baseline.cfg"
cpu_usage: 22.0  # ↑ increased
memory_usage: 43.0
latency_ms: 70.0  # ↑ increased
packet_loss_pct: 35.0  # ↑ HIGH - triggers PACKET_LOSS_INCREASE event
interfaces:
  - name: "GigabitEthernet0/1"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 300  # ↑ significant errors
    tx_errors: 250
    description: "Uplink to distribution"
  - name: "GigabitEthernet0/24"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 400
    tx_errors: 300
    description: "User port - 10.0.1.0/24 subnet"
```

---

### T4 - Interface/Resource Stress (t=180s)

**State:** Sustained degradation, resource exhaustion

**Tags:** `resource_stress`

**Events to Generate:**
- `INTERFACE_DEGRADED` on dist-switch-1
- `CPU_RISE` on edge-router-1

#### edge-router-1
```yaml
timestamp: 180
config_path: "configs/edge-router-1-faulty.cfg"
cpu_usage: 72.0  # ↑ HIGH - triggers CPU_RISE event
memory_usage: 52.0
latency_ms: 85.0  # ↑ worsening
packet_loss_pct: 60.0  # ↑ severe
interfaces:
  - name: "GigabitEthernet0/0"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 1250  # ↑ rapidly increasing
    tx_errors: 890
    description: "LAN-facing interface"
    ip_address: "10.0.0.1/24"
  - name: "GigabitEthernet0/1"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 50
    tx_errors: 30
    description: "Uplink"
    ip_address: "192.168.1.1/24"
```

#### dist-switch-1
```yaml
timestamp: 180
config_path: "configs/dist-switch-1-baseline.cfg"
cpu_usage: 45.0  # ↑ continued increase
memory_usage: 48.0
latency_ms: 90.0  # ↑ severe
packet_loss_pct: 50.0  # ↑ severe
interfaces:
  - name: "GigabitEthernet0/1"
    admin_state: "up"
    oper_state: "degraded"  # ↓ state degraded
    rx_errors: 1250  # ↑ HIGH - triggers INTERFACE_DEGRADED event
    tx_errors: 890
    description: "Uplink to router"
    ip_address: "10.0.0.2/24"
  - name: "GigabitEthernet0/2"
    admin_state: "up"
    oper_state: "degraded"
    rx_errors: 1100
    tx_errors: 800
    description: "Downlink to access"
```

#### access-switch-1
```yaml
timestamp: 180
config_path: "configs/access-switch-1-baseline.cfg"
cpu_usage: 38.0  # ↑ increased
memory_usage: 46.0
latency_ms: 95.0  # ↑ critical
packet_loss_pct: 70.0  # ↑ near-outage
interfaces:
  - name: "GigabitEthernet0/1"
    admin_state: "up"
    oper_state: "degraded"
    rx_errors: 1500
    tx_errors: 1200
    description: "Uplink to distribution"
  - name: "GigabitEthernet0/24"
    admin_state: "up"
    oper_state: "degraded"
    rx_errors: 2000
    tx_errors: 1800
    description: "User port - 10.0.1.0/24 subnet"
```

---

### T5 - Outage (t=240s)

**State:** Complete connectivity loss for 10.0.1.0/24

**Tags:** `outage_peak`

**Events to Generate:**
- `OUTAGE_STARTED` on access-switch-1

**Incident Created:**
- Title: "ACL Regression Blocks Downstream Subnet"
- Status: `active`
- Root device: edge-router-1
- Affected devices: edge-router-1, dist-switch-1, access-switch-1
- Suspicion summary: (generated by correlation engine)

#### edge-router-1
```yaml
timestamp: 240
config_path: "configs/edge-router-1-faulty.cfg"
cpu_usage: 68.0  # stabilizing but high
memory_usage: 53.0
latency_ms: null  # unmeasurable - no response
packet_loss_pct: 100.0  # ↑ TOTAL LOSS
interfaces:
  - name: "GigabitEthernet0/0"
    admin_state: "up"
    oper_state: "up"  # interface still up but blocking all traffic
    rx_errors: 2500
    tx_errors: 1800
    description: "LAN-facing interface"
    ip_address: "10.0.0.1/24"
  - name: "GigabitEthernet0/1"
    admin_state: "up"
    oper_state: "up"
    rx_errors: 100
    tx_errors: 50
    description: "Uplink"
    ip_address: "192.168.1.1/24"
```

#### dist-switch-1
```yaml
timestamp: 240
config_path: "configs/dist-switch-1-baseline.cfg"
cpu_usage: 42.0
memory_usage: 49.0
latency_ms: null
packet_loss_pct: 100.0  # ↑ TOTAL LOSS
interfaces:
  - name: "GigabitEthernet0/1"
    admin_state: "up"
    oper_state: "degraded"
    rx_errors: 2000
    tx_errors: 1500
    description: "Uplink to router"
    ip_address: "10.0.0.2/24"
  - name: "GigabitEthernet0/2"
    admin_state: "up"
    oper_state: "degraded"
    rx_errors: 1800
    tx_errors: 1300
    description: "Downlink to access"
```

#### access-switch-1
```yaml
timestamp: 240
config_path: "configs/access-switch-1-baseline.cfg"
cpu_usage: 35.0
memory_usage: 47.0
latency_ms: null
packet_loss_pct: 100.0  # ↑ TOTAL LOSS - triggers OUTAGE_STARTED
interfaces:
  - name: "GigabitEthernet0/1"
    admin_state: "up"
    oper_state: "degraded"
    rx_errors: 2500
    tx_errors: 2000
    description: "Uplink to distribution"
  - name: "GigabitEthernet0/24"
    admin_state: "up"
    oper_state: "degraded"
    rx_errors: 3000
    tx_errors: 2500
    description: "User port - 10.0.1.0/24 subnet"
```

---

## Configuration Files

### edge-router-1-baseline.cfg

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

### edge-router-1-faulty.cfg

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

### dist-switch-1-baseline.cfg

```cisco
!
hostname dist-switch-1
!
interface GigabitEthernet0/1
 description Uplink to router
 ip address 10.0.0.2 255.255.255.0
 no shutdown
!
interface GigabitEthernet0/2
 description Downlink to access
 switchport mode trunk
 no shutdown
!
line vty 0 4
 login
!
end
```

### access-switch-1-baseline.cfg

```cisco
!
hostname access-switch-1
!
interface GigabitEthernet0/1
 description Uplink to distribution
 switchport mode trunk
 no shutdown
!
interface GigabitEthernet0/24
 description User port - 10.0.1.0/24 subnet
 switchport mode access
 switchport access vlan 10
 no shutdown
!
vlan 10
 name users
!
line vty 0 4
 login
!
end
```

---

## Event Detection Thresholds

### CONFIG_CHANGE
```python
if snapshot.config_hash != previous_snapshot.config_hash:
    emit_event(EventType.CONFIG_CHANGE, severity=INFO)
```

### LATENCY_SPIKE
```python
if snapshot.latency_ms > 50 and previous_snapshot.latency_ms < 30:
    emit_event(EventType.LATENCY_SPIKE, severity=WARNING)
```

### PACKET_LOSS_INCREASE
```python
if snapshot.packet_loss_pct > 20 and previous_snapshot.packet_loss_pct < 10:
    emit_event(EventType.PACKET_LOSS_INCREASE, severity=WARNING)
```

### INTERFACE_DEGRADED
```python
if (snapshot.interface.rx_errors > previous.interface.rx_errors + 1000 or
    snapshot.interface.oper_state == "degraded"):
    emit_event(EventType.INTERFACE_DEGRADED, severity=ERROR)
```

### CPU_RISE
```python
if snapshot.cpu_usage > 70 and previous_snapshot.cpu_usage < 40:
    emit_event(EventType.CPU_RISE, severity=WARNING)
```

### OUTAGE_STARTED
```python
if snapshot.packet_loss_pct >= 80:
    emit_event(EventType.OUTAGE_STARTED, severity=CRITICAL)
    create_incident()
```

---

## JSON Scenario File

**Location:** `packages/mock-scenarios/acl-regression.json`

```json
{
  "scenario_id": "acl-regression-001",
  "name": "ACL Regression Blocks Downstream Subnet",
  "description": "Engineer adds ACL deny rule that blocks downstream subnet",
  "duration_seconds": 240,
  "time_steps": [0, 60, 120, 180, 240],
  "affected_subnet": "10.0.1.0/24",
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
          "cpu_usage": 20.0,
          "memory_usage": 45.0,
          "latency_ms": 7.0,
          "packet_loss_pct": 0.0,
          "tags": ["healthy_baseline"],
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
          ]
        },
        {
          "timestamp": 60,
          "config_path": "configs/edge-router-1-faulty.cfg",
          "cpu_usage": 22.0,
          "memory_usage": 45.0,
          "latency_ms": 8.0,
          "packet_loss_pct": 0.0,
          "tags": ["fault_introduced"],
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
          ]
        }
        // ... continue for T3, T4, T5
      ]
    },
    {
      "device_id": "dist-switch-1",
      "hostname": "dist-switch-1",
      "vendor": "cisco-ios",
      "role": "dist-switch",
      "management_ip": "10.0.0.2",
      "states": [
        // ... T1-T5 states
      ]
    },
    {
      "device_id": "access-switch-1",
      "hostname": "access-switch-1",
      "vendor": "cisco-ios",
      "role": "access-switch",
      "management_ip": "10.0.1.1",
      "states": [
        // ... T1-T5 states
      ]
    }
  ]
}
```

---

## Correlation Expected Output

### Suspicion Summary
```
ACL change on edge-router-1 at 10:23:45Z preceded latency spike and outage. 
New deny rule blocks traffic from affected subnet 10.0.1.0/24.
```

### Correlation Flags
```json
[
  {
    "rule": "recent_config_change_before_degradation",
    "suspicion_level": "high",
    "evidence": "Config change occurred 60s before first degradation event"
  },
  {
    "rule": "acl_deny_affects_subnet",
    "suspicion_level": "high",
    "evidence": "ACL deny rule matches affected subnet 10.0.1.0/24"
  },
  {
    "rule": "time_ordered_primary_suspect",
    "suspicion_level": "high",
    "evidence": "Config change is chronologically first event"
  }
]
```

### Recommendation
```
Review and rollback ACL change on edge-router-1. The deny rule for 10.0.1.0/24 
should be removed or reordered after the permit statement.
```

---

**END OF SCENARIO DEFINITION**
