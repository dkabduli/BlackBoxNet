# BlackBoxNet - Semantic Extraction
## Configuration Parsing and Analysis Rules

**Version:** 1.0  
**Date:** 2024-11-15  
**Scope:** Phase 1 - Cisco IOS ACL Scenario

---

## Table of Contents

1. [Overview](#overview)
2. [Extraction Scope](#extraction-scope)
3. [Cisco IOS Parsing Rules](#cisco-ios-parsing-rules)
4. [Semantic Change Types](#semantic-change-types)
5. [Suspicion Level Assignment](#suspicion-level-assignment)
6. [Implementation Guide](#implementation-guide)
7. [Future Extensions](#future-extensions)

---

## Overview

### Purpose

Semantic extraction transforms raw configuration diffs into structured, meaningful change descriptions that enable correlation and root-cause analysis.

### Phase 1 Goal

**Extract only what's needed for the ACL regression scenario:**
- Interface ACL bindings
- ACL rule definitions
- Deny rules affecting specific subnets
- Basic interface properties

**Do NOT build a full Cisco IOS parser in Phase 1.**

---

## Extraction Scope

### In Scope (Phase 1)

✅ **ACL-Related:**
- ACL number/name detection
- ACL rule parsing (permit/deny, protocol, source, dest)
- Interface ACL binding (`ip access-group`)
- Deny-before-permit pattern detection

✅ **Interface Basics:**
- Interface name
- IP address assignment
- Interface description

✅ **System Basics:**
- Hostname changes

### Out of Scope (Phase 1)

❌ **Deferred to Later Phases:**
- OSPF/BGP/EIGRP neighbor configuration
- Route-map logic
- NAT statements
- QoS policies
- VRF configuration
- VLAN configuration
- EtherChannel/Port-channel
- Crypto/VPN configuration
- SNMP/logging configuration

---

## Cisco IOS Parsing Rules

### Rule 1: ACL Definition Detection

**Pattern:** Standard and Extended ACLs

**Regex Patterns:**
```python
# Standard ACL (1-99, 1300-1999)
STANDARD_ACL = r'^access-list\s+(\d+)\s+(permit|deny)\s+(.+)$'

# Extended ACL (100-199, 2000-2699)
EXTENDED_ACL = r'^access-list\s+(\d+)\s+(permit|deny)\s+(ip|tcp|udp|icmp)\s+(.+)$'

# Named ACL
NAMED_ACL_START = r'^ip\s+access-list\s+(standard|extended)\s+(\S+)$'
NAMED_ACL_RULE = r'^\s+(permit|deny)\s+(ip|tcp|udp|icmp)?\s+(.+)$'
```

**Example Matches:**
```
access-list 100 permit ip any any
  → Standard permit all

access-list 101 deny ip 10.0.1.0 0.0.0.255 any
  → Extended deny from 10.0.1.0/24 to any

access-list 101 permit ip any any
  → Extended permit all
```

**Extracted Data:**
```python
{
    "acl_number": "101",
    "acl_type": "extended",
    "rules": [
        {
            "sequence": 1,
            "action": "deny",
            "protocol": "ip",
            "source": "10.0.1.0 0.0.0.255",
            "source_subnet": "10.0.1.0/24",  # normalized
            "destination": "any"
        },
        {
            "sequence": 2,
            "action": "permit",
            "protocol": "ip",
            "source": "any",
            "destination": "any"
        }
    ]
}
```

---

### Rule 2: Interface ACL Binding

**Pattern:** ACL application to interface

**Regex Pattern:**
```python
INTERFACE_ACL_BINDING = r'^\s+ip\s+access-group\s+(\S+)\s+(in|out)$'
```

**Example Matches:**
```
interface GigabitEthernet0/0
 ip access-group 100 in
   → ACL 100 applied inbound on Gi0/0

 ip access-group EXTERNAL-IN in
   → Named ACL EXTERNAL-IN applied inbound
```

**Extracted Data:**
```python
{
    "interface": "GigabitEthernet0/0",
    "acl": "101",
    "direction": "in"
}
```

---

### Rule 3: Interface IP Address

**Pattern:** IP address assignment

**Regex Pattern:**
```python
IP_ADDRESS = r'^\s+ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)(?:\s+secondary)?$'
```

**Example Matches:**
```
 ip address 10.0.0.1 255.255.255.0
   → Primary IP: 10.0.0.1/24

 ip address 10.0.0.10 255.255.255.0 secondary
   → Secondary IP: 10.0.0.10/24
```

**Extracted Data:**
```python
{
    "interface": "GigabitEthernet0/0",
    "ip_address": "10.0.0.1",
    "netmask": "255.255.255.0",
    "cidr": "10.0.0.1/24",
    "is_secondary": False
}
```

---

### Rule 4: Hostname

**Pattern:** Device hostname

**Regex Pattern:**
```python
HOSTNAME = r'^hostname\s+(\S+)$'
```

**Example:**
```
hostname edge-router-1
  → Hostname: edge-router-1
```

---

### Rule 5: Interface Description

**Pattern:** Interface description text

**Regex Pattern:**
```python
INTERFACE_DESC = r'^\s+description\s+(.+)$'
```

**Example:**
```
 description LAN-facing interface
   → Description: "LAN-facing interface"
```

---

## Semantic Change Types

### Change Type Definitions

Each semantic change has:
- **change_type** - Category of change
- **entity** - What was changed
- **action** - How it changed (added, removed, modified)
- **details** - Specific change data
- **suspicion_level** - How suspicious this change is
- **reason** - Why it's suspicious

---

### 1. ACL_MODIFIED

**When to Emit:**
- ACL rule added
- ACL rule removed
- ACL rule modified

**Example:**
```python
{
    "change_type": "ACL_MODIFIED",
    "entity": "access-list 101",
    "action": "added",  # or "removed", "modified"
    "details": {
        "rule_added": "deny ip 10.0.1.0 0.0.0.255 any",
        "rule_position": 1,
        "position_description": "before permit any",
        "affected_subnet": "10.0.1.0/24",
        "protocol": "ip",
        "action": "deny",
        "source": "10.0.1.0/24",
        "destination": "any"
    },
    "suspicion_level": "high",
    "reason": "Deny rule added before permit affecting subnet 10.0.1.0/24"
}
```

**Suspicion Level Logic:**
```python
def calculate_acl_suspicion(acl_change):
    # High suspicion if:
    # - Deny rule added before permit
    # - Deny rule affects known active subnet
    if acl_change.action == "deny" and acl_change.position == "before permit":
        return "high"
    # - Permit rule removed
    elif acl_change.action == "permit" and acl_change.change == "removed":
        return "medium"
    # - Any other ACL change
    else:
        return "low"
```

---

### 2. INTERFACE_ACL_BINDING

**When to Emit:**
- Interface ACL binding added
- Interface ACL binding removed
- Interface ACL binding modified (different ACL number)

**Example:**
```python
{
    "change_type": "INTERFACE_ACL_BINDING",
    "entity": "GigabitEthernet0/0",
    "action": "modified",  # or "added", "removed"
    "details": {
        "old_acl": "100",
        "new_acl": "101",
        "direction": "in",
        "interface": "GigabitEthernet0/0"
    },
    "suspicion_level": "medium",
    "reason": "ACL binding changed on interface"
}
```

**Suspicion Level Logic:**
```python
def calculate_binding_suspicion(binding_change):
    # Medium suspicion if:
    # - ACL number changed (could indicate logic change)
    if binding_change.old_acl != binding_change.new_acl:
        return "medium"
    # Low suspicion if:
    # - ACL added to interface (new security)
    elif binding_change.action == "added":
        return "low"
    # High suspicion if:
    # - ACL removed from interface (security gap)
    elif binding_change.action == "removed":
        return "high"
```

---

### 3. INTERFACE_IP_CHANGE

**When to Emit:**
- Interface IP address changed
- Interface IP address added
- Interface IP address removed

**Example:**
```python
{
    "change_type": "INTERFACE_IP_CHANGE",
    "entity": "GigabitEthernet0/0",
    "action": "modified",
    "details": {
        "old_ip": "10.0.0.1/24",
        "new_ip": "10.0.0.2/24",
        "interface": "GigabitEthernet0/0"
    },
    "suspicion_level": "medium",
    "reason": "IP address changed on interface"
}
```

---

### 4. HOSTNAME_CHANGE

**When to Emit:**
- Device hostname changed

**Example:**
```python
{
    "change_type": "HOSTNAME_CHANGE",
    "entity": "system",
    "action": "modified",
    "details": {
        "old_hostname": "router-1",
        "new_hostname": "edge-router-1"
    },
    "suspicion_level": "low",
    "reason": "Hostname changed"
}
```

---

## Suspicion Level Assignment

### Suspicion Level Scale

- **critical** - Extremely likely to cause outage (e.g., deny all traffic)
- **high** - Likely related to failure (e.g., deny rule for affected subnet)
- **medium** - Potentially related (e.g., ACL binding change)
- **low** - Unlikely to cause issue (e.g., description change)

### Phase 1 Suspicion Rules

**For ACL Regression Scenario:**

```python
def assign_suspicion_level(semantic_change, affected_subnet="10.0.1.0/24"):
    """
    Assign suspicion level for Phase 1 ACL scenario
    """
    
    if semantic_change.change_type == "ACL_MODIFIED":
        # Check if this is a deny rule
        if semantic_change.details.get("action") == "deny":
            # Check if it affects the known affected subnet
            if affected_subnet in semantic_change.details.get("source", ""):
                # Check if deny is before permit
                if "before permit" in semantic_change.details.get("position_description", ""):
                    return "high", f"Deny rule blocks traffic from {affected_subnet} before permit"
            
        # Other ACL modifications
        return "medium", "ACL rule modified"
    
    elif semantic_change.change_type == "INTERFACE_ACL_BINDING":
        # ACL binding changed
        if semantic_change.action == "modified":
            return "medium", "ACL binding changed on interface"
        elif semantic_change.action == "removed":
            return "high", "ACL protection removed from interface"
        else:
            return "low", "ACL added to interface"
    
    elif semantic_change.change_type == "INTERFACE_IP_CHANGE":
        return "medium", "IP address changed"
    
    elif semantic_change.change_type == "HOSTNAME_CHANGE":
        return "low", "Hostname changed"
    
    else:
        return "low", "Configuration changed"
```

---

## Implementation Guide

### Phase 1 Implementation Strategy

**Use Simple Regex-Based Extraction**

```python
# apps/api/semantic_extraction/cisco_ios.py

import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class SemanticChange:
    change_type: str
    entity: str
    action: str  # added, removed, modified
    details: Dict[str, Any]
    suspicion_level: str
    reason: str

class CiscoIOSExtractor:
    """
    Phase 1: Simple regex-based semantic extraction for ACL scenario
    """
    
    # Regex patterns
    PATTERNS = {
        'acl_extended': re.compile(r'^access-list\s+(\d+)\s+(permit|deny)\s+(ip|tcp|udp|icmp)\s+(.+)$'),
        'interface_acl': re.compile(r'^\s+ip\s+access-group\s+(\S+)\s+(in|out)$'),
        'interface_ip': re.compile(r'^\s+ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+(\d+\.\d+\.\d+\.\d+)'),
        'hostname': re.compile(r'^hostname\s+(\S+)$'),
        'interface_start': re.compile(r'^interface\s+(\S+)$'),
        'description': re.compile(r'^\s+description\s+(.+)$')
    }
    
    def extract_changes(self, diff_text: str, old_config: str, new_config: str) -> List[SemanticChange]:
        """
        Extract semantic changes from config diff
        
        Args:
            diff_text: Unified diff text
            old_config: Previous configuration
            new_config: Current configuration
            
        Returns:
            List of SemanticChange objects
        """
        changes = []
        
        # Parse both configs into structured data
        old_data = self._parse_config(old_config)
        new_data = self._parse_config(new_config)
        
        # Compare ACLs
        changes.extend(self._compare_acls(old_data, new_data))
        
        # Compare interface ACL bindings
        changes.extend(self._compare_interface_acls(old_data, new_data))
        
        # Compare interface IPs
        changes.extend(self._compare_interface_ips(old_data, new_data))
        
        # Compare hostname
        if old_data.get('hostname') != new_data.get('hostname'):
            changes.append(self._create_hostname_change(old_data, new_data))
        
        return changes
    
    def _parse_config(self, config: str) -> Dict[str, Any]:
        """
        Parse config into structured data
        
        Returns dict with:
        - hostname
        - acls: {acl_number: [rules]}
        - interfaces: {interface_name: {acl, ip, description}}
        """
        data = {
            'hostname': None,
            'acls': {},
            'interfaces': {}
        }
        
        current_interface = None
        
        for line in config.split('\n'):
            line = line.rstrip()
            
            # Hostname
            m = self.PATTERNS['hostname'].match(line)
            if m:
                data['hostname'] = m.group(1)
                continue
            
            # Interface start
            m = self.PATTERNS['interface_start'].match(line)
            if m:
                current_interface = m.group(1)
                data['interfaces'][current_interface] = {}
                continue
            
            # Interface ACL binding
            if current_interface:
                m = self.PATTERNS['interface_acl'].match(line)
                if m:
                    data['interfaces'][current_interface]['acl'] = m.group(1)
                    data['interfaces'][current_interface]['acl_direction'] = m.group(2)
                    continue
                
                # Interface IP
                m = self.PATTERNS['interface_ip'].match(line)
                if m:
                    data['interfaces'][current_interface]['ip'] = m.group(1)
                    data['interfaces'][current_interface]['netmask'] = m.group(2)
                    continue
                
                # Description
                m = self.PATTERNS['description'].match(line)
                if m:
                    data['interfaces'][current_interface]['description'] = m.group(1)
                    continue
            
            # ACL rules
            m = self.PATTERNS['acl_extended'].match(line)
            if m:
                acl_num = m.group(1)
                action = m.group(2)
                protocol = m.group(3)
                rest = m.group(4)
                
                if acl_num not in data['acls']:
                    data['acls'][acl_num] = []
                
                data['acls'][acl_num].append({
                    'action': action,
                    'protocol': protocol,
                    'params': rest,
                    'line': line
                })
        
        return data
    
    def _compare_acls(self, old_data: Dict, new_data: Dict) -> List[SemanticChange]:
        """Compare ACL definitions"""
        changes = []
        
        # Find added ACLs
        for acl_num in new_data['acls']:
            if acl_num not in old_data['acls']:
                # New ACL added
                changes.append(self._create_acl_change(acl_num, new_data['acls'][acl_num], 'added'))
        
        # Find modified ACLs
        for acl_num in new_data['acls']:
            if acl_num in old_data['acls']:
                if old_data['acls'][acl_num] != new_data['acls'][acl_num]:
                    # ACL modified
                    changes.append(self._create_acl_change(
                        acl_num, 
                        new_data['acls'][acl_num],
                        'modified',
                        old_rules=old_data['acls'][acl_num]
                    ))
        
        return changes
    
    def _create_acl_change(self, acl_num: str, rules: List[Dict], action: str, old_rules: List[Dict] = None) -> SemanticChange:
        """Create semantic change for ACL modification"""
        
        # Check for deny-before-permit pattern
        has_deny_before_permit = False
        denied_subnet = None
        
        for i, rule in enumerate(rules):
            if rule['action'] == 'deny':
                # Check if there's a permit after this
                for later_rule in rules[i+1:]:
                    if later_rule['action'] == 'permit':
                        has_deny_before_permit = True
                        
                        # Extract subnet from params
                        # Format: "ip 10.0.1.0 0.0.0.255 any"
                        parts = rule['params'].split()
                        if len(parts) >= 2:
                            denied_subnet = self._wildcard_to_cidr(parts[0], parts[1])
                        break
        
        # Determine suspicion level
        suspicion_level = "low"
        reason = f"ACL {acl_num} {action}"
        
        if has_deny_before_permit and denied_subnet:
            suspicion_level = "high"
            reason = f"Deny rule added before permit affecting subnet {denied_subnet}"
        elif action == "added":
            suspicion_level = "medium"
            reason = f"New ACL {acl_num} created"
        
        details = {
            "acl_number": acl_num,
            "rules": rules,
            "has_deny_before_permit": has_deny_before_permit,
            "denied_subnet": denied_subnet
        }
        
        if old_rules:
            details["old_rules"] = old_rules
        
        return SemanticChange(
            change_type="ACL_MODIFIED",
            entity=f"access-list {acl_num}",
            action=action,
            details=details,
            suspicion_level=suspicion_level,
            reason=reason
        )
    
    def _wildcard_to_cidr(self, ip: str, wildcard: str) -> str:
        """Convert wildcard mask to CIDR notation"""
        # Simple conversion for common masks
        wildcard_to_prefix = {
            '0.0.0.255': '24',
            '0.0.255.255': '16',
            '0.255.255.255': '8'
        }
        prefix = wildcard_to_prefix.get(wildcard, '??')
        return f"{ip}/{prefix}"
    
    def _compare_interface_acls(self, old_data: Dict, new_data: Dict) -> List[SemanticChange]:
        """Compare interface ACL bindings"""
        changes = []
        
        for interface in new_data['interfaces']:
            old_acl = old_data['interfaces'].get(interface, {}).get('acl')
            new_acl = new_data['interfaces'][interface].get('acl')
            
            if old_acl != new_acl:
                action = 'modified' if old_acl and new_acl else ('added' if new_acl else 'removed')
                changes.append(SemanticChange(
                    change_type="INTERFACE_ACL_BINDING",
                    entity=interface,
                    action=action,
                    details={
                        "interface": interface,
                        "old_acl": old_acl,
                        "new_acl": new_acl,
                        "direction": new_data['interfaces'][interface].get('acl_direction', 'in')
                    },
                    suspicion_level="medium",
                    reason=f"ACL binding changed on {interface}"
                ))
        
        return changes
    
    def _compare_interface_ips(self, old_data: Dict, new_data: Dict) -> List[SemanticChange]:
        """Compare interface IP addresses"""
        changes = []
        
        for interface in new_data['interfaces']:
            old_ip = old_data['interfaces'].get(interface, {}).get('ip')
            new_ip = new_data['interfaces'][interface].get('ip')
            
            if old_ip != new_ip and new_ip:
                changes.append(SemanticChange(
                    change_type="INTERFACE_IP_CHANGE",
                    entity=interface,
                    action="modified",
                    details={
                        "interface": interface,
                        "old_ip": old_ip,
                        "new_ip": new_ip
                    },
                    suspicion_level="medium",
                    reason=f"IP address changed on {interface}"
                ))
        
        return changes
    
    def _create_hostname_change(self, old_data: Dict, new_data: Dict) -> SemanticChange:
        """Create hostname change semantic change"""
        return SemanticChange(
            change_type="HOSTNAME_CHANGE",
            entity="system",
            action="modified",
            details={
                "old_hostname": old_data.get('hostname'),
                "new_hostname": new_data.get('hostname')
            },
            suspicion_level="low",
            reason="Hostname changed"
        )
```

---

## Future Extensions

### Phase 2: Deeper Cisco IOS Parsing

**Add Support For:**
- OSPF configuration changes
- BGP peer configuration
- Route-map logic
- NAT statements
- Static route changes
- Interface state changes (shutdown/no shutdown)

### Phase 3: Multi-Vendor Support

**Junos Parsing:**
- Set-style configuration
- Firewall filter semantics
- Policy-options
- Routing-instances

**Nokia SR OS Parsing:**
- MD-CLI syntax
- Service configuration
- MPLS/VPN semantics

---

**END OF SEMANTIC EXTRACTION DOCUMENT**
