#!/usr/bin/env python3
"""Generate Phase 2 scenario JSON fixtures and namespaced config snapshots."""
from __future__ import annotations

import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.join(ROOT, "packages", "mock-scenarios")
OLD_CFG = os.path.join(PKG, "configs")
ACL_SRC = {
    "edge-router-1": {
        "T1": "edge-router-1-baseline.cfg",
        "T2": "edge-router-1-faulty.cfg",
        "T3": "edge-router-1-faulty.cfg",
        "T4": "edge-router-1-faulty.cfg",
        "T5": "edge-router-1-faulty.cfg",
    },
    "dist-switch-1": {f"T{i}": "dist-switch-1-baseline.cfg" for i in range(1, 6)},
    "access-switch-1": {f"T{i}": "access-switch-1-baseline.cfg" for i in range(1, 6)},
}

TIMES = [0, 60, 120, 180, 240]
TAGS = ["healthy_baseline", "fault_introduced", "degradation_detected", "resource_stress", "outage_peak"]


def write_config(scenario: str, device: str, step: str, content: str) -> str:
    rel = f"configs/{scenario}/{device}/{step}.txt"
    path = os.path.join(PKG, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return rel


def iface(name: str, oper="up", rx=0, tx=0, desc=None, ip=None):
    return {
        "name": name,
        "admin_state": "up",
        "oper_state": oper,
        "rx_errors": rx,
        "tx_errors": tx,
        "description": desc,
        "ip_address": ip,
    }


def device_states(device_id, hostname, vendor, role, mgmt, configs, metrics):
    states = []
    for i, t in enumerate(TIMES):
        m = metrics[i]
        states.append(
            {
                "timestamp": t,
                "config_path": configs[i],
                "cpu_usage": m["cpu"],
                "memory_usage": m["mem"],
                "latency_ms": m.get("lat"),
                "packet_loss_pct": m["pkt"],
                "tags": [TAGS[i]],
                "interfaces": m.get("ifaces", []),
            }
        )
    return {
        "device_id": device_id,
        "hostname": hostname,
        "vendor": vendor,
        "role": role,
        "management_ip": mgmt,
        "states": states,
    }


def migrate_acl_configs():
    for device, steps in ACL_SRC.items():
        for step, src_name in steps.items():
            src = os.path.join(OLD_CFG, src_name)
            if os.path.exists(src):
                with open(src, encoding="utf-8") as f:
                    content = f.read()
            else:
                content = f"! placeholder {device} {step}\n"
            write_config("acl-regression", device, step, content)


def nokia_p_router(step: str) -> str:
    if step == "T1":
        return """configure router
    ldp
        interface-parameters
            interface "toPE1" { }
            interface "toPE2" { }
        exit
        targeted-session
        exit
        fec-originate 10.0.1.0/24
        fec-originate 10.0.2.0/24
    exit
exit
"""
    return """configure router
    ldp
        interface-parameters
            interface "toPE1" { }
            interface "toPE2" { }
            interface "toNewPeer" { }
        exit
        targeted-session
            peer 10.0.9.1 create
                hello 15 45
                keepalive 30 3
            exit
        exit
        fec-originate 10.0.1.0/24
        fec-originate 10.0.2.0/24
        fec-originate 10.0.5.0/24
            static-label-map 131071
        exit
    exit
exit
"""


def ospf_r1(step: str) -> str:
    base = """router ospf 1
 router-id 1.1.1.1
 network 10.0.0.0 0.0.0.255 area 0
 network 10.1.0.0 0.0.0.255 area 0
"""
    if step in ("T1",):
        return base + "interface Serial0/0/0\n ip ospf hello-interval 10\n ip ospf dead-interval 40\n"
    return base + "interface Serial0/0/0\n ip ospf hello-interval 5\n ip ospf dead-interval 20\n"


def ospf_peer(step: str) -> str:
    return """router ospf 1
 router-id 3.3.3.3
 network 10.1.0.0 0.0.0.255 area 1
interface Serial0/0/0
 ip ospf hello-interval 10
 ip ospf dead-interval 40
"""


def bgp_edge(step: str) -> str:
    if step == "T1":
        return """router bgp 65001
 address-family ipv4
  neighbor 203.0.113.1 route-map EXPORT-OUT out
route-map EXPORT-OUT permit 10
 set community no-export
"""
    return """router bgp 65001
 address-family ipv4
  neighbor 203.0.113.1 route-map EXPORT-OUT out
route-map EXPORT-OUT permit 10
 set community none
"""


def stp_sw(name: str, step: str, priority: int) -> str:
    return f"""hostname {name}
spanning-tree vlan 1 priority {priority}
interface GigabitEthernet0/1
 switchport mode trunk
"""


def build_acl_regression():
    migrate_acl_configs()
    devices = []
    acl_metrics = {
        "edge-router-1": [
            {"cpu": 20, "mem": 45, "lat": 7, "pkt": 0},
            {"cpu": 22, "mem": 45, "lat": 8, "pkt": 0},
            {"cpu": 35, "mem": 48, "lat": 55, "pkt": 10},
            {"cpu": 72, "mem": 52, "lat": 85, "pkt": 60},
            {"cpu": 68, "mem": 53, "lat": None, "pkt": 100},
        ],
        "dist-switch-1": [
            {"cpu": 18, "mem": 42, "lat": 8, "pkt": 0},
            {"cpu": 18, "mem": 42, "lat": 8, "pkt": 0},
            {"cpu": 28, "mem": 44, "lat": 65, "pkt": 15},
            {"cpu": 45, "mem": 48, "lat": 90, "pkt": 50},
            {"cpu": 42, "mem": 49, "lat": None, "pkt": 100},
        ],
        "access-switch-1": [
            {"cpu": 15, "mem": 40, "lat": 9, "pkt": 0},
            {"cpu": 15, "mem": 40, "lat": 9, "pkt": 0},
            {"cpu": 22, "mem": 43, "lat": 70, "pkt": 35},
            {"cpu": 38, "mem": 46, "lat": 95, "pkt": 70},
            {"cpu": 35, "mem": 47, "lat": None, "pkt": 100},
        ],
    }
    for dev, metrics in acl_metrics.items():
        configs = [f"configs/acl-regression/{dev}/T{i}.txt" for i in range(1, 6)]
        role = "edge-router" if "edge" in dev else ("dist-switch" if "dist" in dev else "access-switch")
        devices.append(
            device_states(dev, dev, "cisco-ios", role, "10.0.0.1" if dev == "edge-router-1" else "10.0.0.2", configs, metrics)
        )
    return {
        "id": "acl-regression",
        "label": "ACL Regression",
        "vendor": "cisco-ios",
        "tab_order": 1,
        "topology_type": "linear",
        "name": "ACL Regression Blocks Downstream Subnet",
        "description": "Engineer adds ACL deny rule that blocks downstream subnet",
        "duration_seconds": 240,
        "time_steps": TIMES,
        "affected_subnet": "10.0.1.0/24",
        "demo_path": "PC 10.0.1.0/24 -> access-switch-1 -> dist-switch-1 -> edge-router-1",
        "step_labels": {
            "T1": "Baseline healthy",
            "T2": "ACL change introduced",
            "T3": "Degradation detected",
            "T4": "Resource stress",
            "T5": "Outage peak",
        },
        "correlation": {
            "incident_title": "ACL Regression Blocks Downstream Subnet",
            "root_device": "edge-router-1",
            "recommendation": "Review and rollback ACL change on edge-router-1.",
        },
        "correlation_rules": [{"id": "acl-deny-subnet", "pattern": "acl_deny_subnet"}],
        "devices": devices,
    }


def build_ospf():
    routers = [("R1", "core-router", "1.1.1.1"), ("R2", "core-router", "2.2.2.2"), ("R3", "core-router", "3.3.3.3"), ("R4", "core-router", "4.4.4.4")]
    devices = []
    pkt_progression = [0, 0, 5, 40, 100]
    cpu = [[18, 20, 45, 78, 85], [17, 18, 42, 75, 80], [16, 18, 50, 70, 95], [16, 17, 48, 68, 92]]
    for idx, (rid, role, ip) in enumerate(routers):
        configs = []
        for s in range(1, 6):
            step = f"T{s}"
            content = ospf_r1(step) if rid == "R1" else ospf_peer(step)
            rel = write_config("ospf-multiarea", rid, step, content)
            configs.append(rel)
        metrics = [
            {"cpu": cpu[idx][i], "mem": 40 + i, "lat": 5 if i < 2 else (40 if i < 4 else None), "pkt": pkt_progression[i]}
            for i in range(5)
        ]
        devices.append(device_states(rid, rid, "cisco-ios", role, ip, configs, metrics))
    return {
        "id": "ospf-multiarea",
        "label": "OSPF Multi-Area",
        "vendor": "cisco-ios",
        "tab_order": 2,
        "topology_type": "ospf-multiarea",
        "name": "OSPF Multi-Area Adjacency Flap",
        "description": "Hello/dead timer mismatch causes area partition",
        "duration_seconds": 240,
        "time_steps": TIMES,
        "affected_subnet": "10.1.0.0/24",
        "demo_path": "Area 1/2 IRs via ABRs R1/R2 in Area 0",
        "step_labels": {
            "T1": "All adjacencies FULL",
            "T2": "R1 timer change pushed",
            "T3": "Adjacency EXSTART / LSA flood",
            "T4": "Inter-area routes lost",
            "T5": "Areas partitioned — outage",
        },
        "correlation": {
            "incident_title": "OSPF Area Partition from Timer Mismatch",
            "root_device": "R1",
            "recommendation": "Align hello/dead timers on R1 Serial0/0/0 with R3/R4.",
        },
        "correlation_rules": [{"id": "ospf-timer-mismatch", "pattern": "ospf_timer_mismatch"}],
        "devices": devices,
    }


def build_nokia():
    devices = []
    specs = [
        ("p-router", "core-router", "10.0.0.1", "nokia-sros"),
        ("pe-1", "edge-router", "10.0.1.1", "nokia-sros"),
        ("pe-2", "edge-router", "10.0.2.1", "nokia-sros"),
    ]
    pkt = [[0, 0, 15, 60, 100], [0, 0, 20, 70, 100], [0, 0, 10, 55, 100]]
    for i, (did, role, ip, vendor) in enumerate(specs):
        configs = []
        for s in range(1, 6):
            step = f"T{s}"
            content = nokia_p_router(step) if did == "p-router" else f"configure service\n  customer 1 create\n    description PE {did}\n"
            rel = write_config("nokia-ldp-collision", did, step, content)
            configs.append(rel)
        metrics = [{"cpu": 20 + j, "mem": 42, "lat": 4 if j < 2 else (50 if j < 4 else None), "pkt": pkt[i][j]} for j in range(5)]
        devices.append(device_states(did, did, vendor, role, ip, configs, metrics))
    return {
        "id": "nokia-ldp-collision",
        "label": "LDP Collision",
        "vendor": "nokia-sros",
        "tab_order": 10,
        "topology_type": "nokia-hub",
        "name": "Nokia LDP Label Collision",
        "description": "Static label 131071 overwrites active LFIB binding",
        "duration_seconds": 240,
        "time_steps": TIMES,
        "affected_subnet": "10.0.1.0/24",
        "demo_path": "PE-1/PE-2 via P-router MPLS core",
        "step_labels": {
            "T1": "Healthy MPLS core",
            "T2": "Static label 131071 assigned",
            "T3": "LFIB silent overwrite",
            "T4": "LSP black-hole detected",
            "T5": "Full LSP failure",
        },
        "correlation": {
            "incident_title": "LDP Label Collision — LFIB Overwrite",
            "root_device": "p-router",
            "recommendation": "Remove static-label-map 131071 on new FEC 10.0.5.0/24.",
        },
        "correlation_rules": [{"id": "ldp-label-collision", "pattern": "ldp_label_collision"}],
        "devices": devices,
    }


def build_bgp():
    devices = []
    names = [("edge-router-1", "edge-router"), ("core-router-1", "core-router"), ("rr-1", "core-router")]
    for did, role in names:
        configs = []
        for s in range(1, 6):
            step = f"T{s}"
            content = bgp_edge(step) if did == "edge-router-1" else f"router bgp 65001\n neighbor {did}\n"
            rel = write_config("bgp-route-leak", did, step, content)
            configs.append(rel)
        metrics = [{"cpu": 18 + s, "mem": 40, "lat": 6 if s < 3 else None, "pkt": [0, 0, 10, 45, 100][s]} for s in range(5)]
        devices.append(device_states(did, did, "cisco-ios", role, f"10.0.{names.index((did, role))}.1", configs, metrics))
    return {
        "id": "bgp-route-leak",
        "label": "BGP Leak",
        "vendor": "cisco-ios",
        "tab_order": 4,
        "topology_type": "bgp-triangle",
        "name": "BGP Route Leak",
        "description": "no-export community stripped on eBGP export",
        "duration_seconds": 240,
        "time_steps": TIMES,
        "affected_subnet": "10.10.0.0/16",
        "demo_path": "iBGP mesh + upstream eBGP peer",
        "step_labels": {
            "T1": "Healthy BGP sessions",
            "T2": "route-map strips no-export",
            "T3": "Upstream receives leaked prefixes",
            "T4": "WITHDRAW cascade",
            "T5": "Reachability loss",
        },
        "correlation": {
            "incident_title": "BGP Route Leak to Upstream",
            "root_device": "edge-router-1",
            "recommendation": "Restore set community no-export on EXPORT-OUT.",
        },
        "correlation_rules": [{"id": "bgp-community-stripped", "pattern": "bgp_community_stripped"}],
        "devices": devices,
    }


def build_stp():
    switches = [("core-1", 4096), ("dist-1", 8192), ("dist-2", 8192), ("access-1", 16384), ("rogue-1", 0)]
    devices = []
    for did, prio in switches:
        configs = []
        for s in range(1, 6):
            step = f"T{s}"
            p = prio if (did != "rogue-1" or s < 2) else 0
            rel = write_config("stp-root-hijack", did, step, stp_sw(did, step, p))
            configs.append(rel)
        pkt = [0, 0, 15, 55, 100] if did == "rogue-1" else [0, 0, 10, 40, 95]
        metrics = [{"cpu": 15 + s * 8, "mem": 40, "lat": 5 if s < 3 else None, "pkt": pkt[s]} for s in range(5)]
        role = "access-switch" if "access" in did or did == "rogue-1" else "dist-switch"
        devices.append(device_states(did, did, "cisco-ios", role, f"10.0.{switches.index((did, prio))}.10", configs, metrics))
    return {
        "id": "stp-root-hijack",
        "label": "STP Root Hijack",
        "vendor": "cisco-ios",
        "tab_order": 5,
        "topology_type": "stp-star",
        "name": "STP Root Bridge Hijack",
        "description": "Rogue switch priority 0 triggers TCN storm",
        "duration_seconds": 240,
        "time_steps": TIMES,
        "affected_subnet": "10.0.50.0/24",
        "demo_path": "5-switch campus — rogue access switch",
        "step_labels": {
            "T1": "Stable STP topology",
            "T2": "Rogue switch added (priority 0)",
            "T3": "Root re-election",
            "T4": "TCN flooding",
            "T5": "Broadcast storm / blackout",
        },
        "correlation": {
            "incident_title": "STP Root Hijack — TCN Storm",
            "root_device": "rogue-1",
            "recommendation": "Remove rogue switch or raise its spanning-tree priority.",
        },
        "correlation_rules": [{"id": "stp-priority-subversion", "pattern": "stp_priority_subversion"}],
        "devices": devices,
    }


def juniper_edge(step: str) -> str:
    base = """system {
    host-name edge-router;
}
protocols {
    bgp {
        group upstream {
            type external;
            neighbor 203.0.113.1 {
"""
    if step == "T1":
        return base + "                hold-time 90;\n            }\n        }\n    }\n}\n"
    return base + "                hold-time 30;\n            }\n        }\n    }\n}\n"


def _metrics_progression():
    return [
        {"cpu": 18, "mem": 42, "lat": 5, "pkt": 0},
        {"cpu": 19, "mem": 42, "lat": 6, "pkt": 0},
        {"cpu": 22, "mem": 44, "lat": 40, "pkt": 12},
        {"cpu": 28, "mem": 46, "lat": 55, "pkt": 55},
        {"cpu": 30, "mem": 48, "lat": None, "pkt": 100},
    ]


def juniper_isis_pe(step: str) -> str:
    base = """protocols {
    isis {
        interface ge-0/0/1.0 {
            level 2 {
"""
    if step == "T1":
        return base + "                metric 10;\n            }\n        }\n    }\n}\n"
    return base + "                wide-metric 1000000;\n            }\n        }\n    }\n}\n"


def juniper_rsvp_transit(step: str) -> str:
    if step == "T1":
        return """protocols {
    mpls {
        path LSP-PRIMARY {
            bandwidth 10g;
        }
    }
}
"""
    return """protocols {
    mpls {
        path LSP-PRIMARY {
            bandwidth 1m;
        }
    }
}
"""


def juniper_srx_policer(step: str) -> str:
    if step == "T1":
        return """security {
    policer voice-policer {
        bandwidth-limit 100m;
        loss-priority high;
    }
}
"""
    return """security {
    policer voice-policer {
        bandwidth-limit 100m;
        loss-priority low;
    }
}
"""


def nokia_sdp_pe(step: str) -> str:
    if step == "T1":
        return """configure service
    sdp 100 create
        far-end 10.0.0.2
        ldp
    exit
exit
"""
    return """configure service
    sdp 100 create
        far-end 10.0.0.99
        ldp
    exit
exit
"""


def nokia_vprn_hub(step: str) -> str:
    if step == "T1":
        return """configure service
    vprn 100 customer 1 create
        route-distinguisher 65000:100
        vrf-export VPRN100-EXPORT
    exit
exit
"""
    return """configure service
    vprn 100 customer 1 create
        route-distinguisher 65000:100
        vrf-export VPRN200-EXPORT
    exit
exit
"""


def nokia_qos_access(step: str) -> str:
    if step == "T1":
        return """configure qos
    sap-ingress 10 create
        policer 1 create
            rate 10000 cir 10000
        exit
    exit
exit
"""
    return """configure qos
    sap-ingress 10 create
        policer 1 create
            rate 1000 cir 1000
        exit
    exit
exit
"""


def build_juniper_isis():
    sid = "juniper-isis-metric"
    specs = [("ce-1", "edge-router", "10.20.0.1"), ("pe-1", "pe-router", "10.20.0.2"), ("p-1", "core-router", "10.20.0.3")]
    devices = []
    for did, role, ip in specs:
        configs = []
        for s in range(1, 6):
            step = f"T{s}"
            if did == "pe-1":
                content = juniper_isis_pe(step)
            elif did == "p-1":
                content = "protocols { isis { interface lo0.0; } }\n"
            else:
                content = f"protocols {{ isis {{ interface ge-0/0/0.0; }} }}\n"
            rel = write_config(sid, did, step, content)
            configs.append(rel)
        devices.append(device_states(did, did, "junos", role, ip, configs, _metrics_progression()))
    return {
        "id": sid,
        "label": "IS-IS Wide Metric",
        "vendor": "junos",
        "tab_order": 7,
        "topology_type": "linear",
        "name": "Junos IS-IS Wide-Metric Leak",
        "description": "Aggressive wide-metric on PE starves CE return path",
        "duration_seconds": 240,
        "time_steps": TIMES,
        "affected_subnet": "10.20.0.0/24",
        "demo_path": "CE → PE → P (IS-IS L2 core)",
        "step_labels": {
            "T1": "IS-IS adjacencies UP",
            "T2": "wide-metric 1M on PE",
            "T3": "CE route timeout",
            "T4": "LSP churn / blackhole",
            "T5": "Subscriber outage",
        },
        "correlation": {
            "incident_title": "IS-IS Wide-Metric Blackhole on PE",
            "root_device": "pe-1",
            "recommendation": "Restore IS-IS interface metric 10 on PE ge-0/0/1.",
        },
        "correlation_rules": [{"id": "junos-isis-metric", "pattern": "junos_isis_metric"}],
        "devices": devices,
    }


def build_juniper_rsvp():
    sid = "juniper-rsvp-te"
    specs = [
        ("ingress-pe", "pe-router", "10.30.0.1"),
        ("transit-p", "core-router", "10.30.0.2"),
        ("egress-pe", "pe-router", "10.30.0.3"),
    ]
    devices = []
    for did, role, ip in specs:
        configs = []
        for s in range(1, 6):
            step = f"T{s}"
            content = juniper_rsvp_transit(step) if did == "transit-p" else f"protocols {{ mpls {{ lsp EGRESS; }} }}\n"
            rel = write_config(sid, did, step, content)
            configs.append(rel)
        devices.append(device_states(did, did, "junos", role, ip, configs, _metrics_progression()))
    return {
        "id": sid,
        "label": "RSVP-TE LSP",
        "vendor": "junos",
        "tab_order": 8,
        "topology_type": "junos-triangle",
        "name": "Junos RSVP-TE Bandwidth Collapse",
        "description": "LSP bandwidth cut to 1Mbps on 10G trunk",
        "duration_seconds": 240,
        "time_steps": TIMES,
        "affected_subnet": "10.30.0.0/24",
        "demo_path": "Ingress PE → P → Egress PE MPLS",
        "step_labels": {
            "T1": "RSVP LSPs UP",
            "T2": "bandwidth 1m applied",
            "T3": "Soft-preempt timeouts",
            "T4": "LSP DOWN events",
            "T5": "MPLS service outage",
        },
        "correlation": {
            "incident_title": "RSVP-TE Bandwidth Starvation",
            "root_device": "transit-p",
            "recommendation": "Restore RSVP path bandwidth to 10g on transit-p.",
        },
        "correlation_rules": [{"id": "junos-rsvp-te", "pattern": "junos_rsvp_te"}],
        "devices": devices,
    }


def build_juniper_policer():
    sid = "juniper-firewall-policer"
    specs = [
        ("edge-router", "edge-router", "10.40.0.1"),
        ("srx-gw", "firewall", "10.40.0.2"),
        ("core-rr", "core-router", "10.40.0.3"),
    ]
    devices = []
    for did, role, ip in specs:
        configs = []
        for s in range(1, 6):
            step = f"T{s}"
            content = juniper_srx_policer(step) if did == "srx-gw" else f"protocols {{ bgp {{ group internal; }} }}\n"
            rel = write_config(sid, did, step, content)
            configs.append(rel)
        devices.append(device_states(did, did, "junos", role, ip, configs, _metrics_progression()))
    return {
        "id": sid,
        "label": "SRX Policer",
        "vendor": "junos",
        "tab_order": 9,
        "topology_type": "linear",
        "name": "Junos SRX Loss-Priority Policer",
        "description": "Policer loss-priority low drops voice despite ample bandwidth",
        "duration_seconds": 240,
        "time_steps": TIMES,
        "affected_subnet": "10.40.0.0/24",
        "demo_path": "Edge → SRX → RR (services)",
        "step_labels": {
            "T1": "Policer baseline",
            "T2": "loss-priority low",
            "T3": "Voice RTP drops",
            "T4": "Alarm flood",
            "T5": "Access outage",
        },
        "correlation": {
            "incident_title": "SRX Policer Misclassification",
            "root_device": "srx-gw",
            "recommendation": "Set loss-priority high on voice-policer.",
        },
        "correlation_rules": [{"id": "junos-policer", "pattern": "junos_policer"}],
        "devices": devices,
    }


def build_nokia_sdp():
    sid = "nokia-sdp-blackhole"
    specs = [("pe-core", "core-router", "10.50.0.1"), ("pe-agg", "edge-router", "10.50.0.2")]
    devices = []
    for did, role, ip in specs:
        configs = []
        for s in range(1, 6):
            step = f"T{s}"
            content = nokia_sdp_pe(step) if did == "pe-core" else "configure service\n  epipe 1 customer 1 create\n"
            rel = write_config(sid, did, step, content)
            configs.append(rel)
        devices.append(device_states(did, did, "nokia-sros", role, ip, configs, _metrics_progression()))
    return {
        "id": sid,
        "label": "SDP Blackhole",
        "vendor": "nokia-sros",
        "tab_order": 11,
        "topology_type": "nokia-hub",
        "name": "Nokia SDP Spoke Blackhole",
        "description": "SDP far-end rewritten to unreachable PE",
        "duration_seconds": 240,
        "time_steps": TIMES,
        "affected_subnet": "10.50.0.0/24",
        "demo_path": "PE-core → PE-agg → SDP binding",
        "step_labels": {
            "T1": "SDP/IES healthy",
            "T2": "far-end 10.0.0.99",
            "T3": "Spoke-SDP DOWN",
            "T4": "MAC withdraw storm",
            "T5": "Service DOWN",
        },
        "correlation": {
            "incident_title": "SDP Far-End Blackhole",
            "root_device": "pe-core",
            "recommendation": "Restore SDP 100 far-end to 10.0.0.2.",
        },
        "correlation_rules": [{"id": "nokia-sdp-blackhole", "pattern": "nokia_sdp_blackhole"}],
        "devices": devices,
    }


def build_nokia_vprn():
    sid = "nokia-vprn-leak"
    specs = [
        ("pe-hub", "core-router", "10.60.0.1"),
        ("pe-1", "edge-router", "10.60.0.2"),
        ("pe-2", "edge-router", "10.60.0.3"),
    ]
    devices = []
    for did, role, ip in specs:
        configs = []
        for s in range(1, 6):
            step = f"T{s}"
            content = nokia_vprn_hub(step) if did == "pe-hub" else f"configure service\n  vprn customer {did}\n"
            rel = write_config(sid, did, step, content)
            configs.append(rel)
        devices.append(device_states(did, did, "nokia-sros", role, ip, configs, _metrics_progression()))
    return {
        "id": sid,
        "label": "VPRN Leak",
        "vendor": "nokia-sros",
        "tab_order": 12,
        "topology_type": "nokia-hub",
        "name": "Nokia VPRN Export Leak",
        "description": "VPRN 100 export-policy points at VPRN 200 routes",
        "duration_seconds": 240,
        "time_steps": TIMES,
        "affected_subnet": "10.60.0.0/24",
        "demo_path": "PE-hub ↔ PE-1 / PE-2 VPRN mesh",
        "step_labels": {
            "T1": "VPRN routes stable",
            "T2": "export-policy swap",
            "T3": "RT leak detected",
            "T4": "BGP VPNv4 churn",
            "T5": "Customer isolation lost",
        },
        "correlation": {
            "incident_title": "VPRN Export Policy Leak",
            "root_device": "pe-hub",
            "recommendation": "Restore vrf-export VPRN100-EXPORT on VPRN 100.",
        },
        "correlation_rules": [{"id": "nokia-vprn-leak", "pattern": "nokia_vprn_leak"}],
        "devices": devices,
    }


def build_nokia_qos():
    sid = "nokia-qos-policer"
    specs = [
        ("pe-access", "edge-router", "10.70.0.1"),
        ("pe-agg", "core-router", "10.70.0.2"),
        ("p-router", "core-router", "10.70.0.3"),
    ]
    devices = []
    for did, role, ip in specs:
        configs = []
        for s in range(1, 6):
            step = f"T{s}"
            content = nokia_qos_access(step) if did == "pe-access" else f"configure router\n  interface {did}\n"
            rel = write_config(sid, did, step, content)
            configs.append(rel)
        devices.append(device_states(did, did, "nokia-sros", role, ip, configs, _metrics_progression()))
    return {
        "id": sid,
        "label": "QoS Policer",
        "vendor": "nokia-sros",
        "tab_order": 13,
        "topology_type": "linear",
        "name": "Nokia Ingress Policer Starvation",
        "description": "Access policer cut to 1 Mbps on 10G SAP",
        "duration_seconds": 240,
        "time_steps": TIMES,
        "affected_subnet": "10.70.0.0/24",
        "demo_path": "Access PE → Agg → P",
        "step_labels": {
            "T1": "QoS baseline",
            "T2": "policer 1 Mbps",
            "T3": "Queue drops spike",
            "T4": "SAP congestion",
            "T5": "Subscriber throttle",
        },
        "correlation": {
            "incident_title": "Ingress Policer Misconfiguration",
            "root_device": "pe-access",
            "recommendation": "Restore policer rate 10000 on sap-ingress 10.",
        },
        "correlation_rules": [{"id": "nokia-qos-policer", "pattern": "nokia_qos_policer"}],
        "devices": devices,
    }


def build_juniper():
    devices = []
    specs = [
        ("edge-router", "edge-router", "10.0.0.1"),
        ("rr-1", "core-router", "10.0.0.2"),
        ("pe-1", "edge-router", "10.0.1.1"),
    ]
    for i, (did, role, ip) in enumerate(specs):
        configs = []
        for s in range(1, 6):
            step = f"T{s}"
            content = juniper_edge(step) if did == "edge-router" else f"protocols {{ bgp {{ group internal; }} }}\n"
            rel = write_config("juniper-bgp-hold", did, step, content)
            configs.append(rel)
        metrics = [
            {"cpu": 18 + j, "mem": 42, "lat": 5 if j < 2 else (45 if j < 4 else None), "pkt": [0, 0, 12, 50, 100][j]}
            for j in range(5)
        ]
        devices.append(device_states(did, did, "junos", role, ip, configs, metrics))
    return {
        "id": "juniper-bgp-hold",
        "label": "BGP Hold Timer",
        "vendor": "junos",
        "tab_order": 6,
        "topology_type": "junos-triangle",
        "name": "Juniper BGP Hold-Timer Mismatch",
        "description": "Aggressive hold-time causes repeated BGP session resets",
        "duration_seconds": 240,
        "time_steps": TIMES,
        "affected_subnet": "10.0.10.0/24",
        "demo_path": "Junos edge → RR → PE eBGP/iBGP path",
        "step_labels": {
            "T1": "BGP sessions established",
            "T2": "hold-time reduced to 30s",
            "T3": "Flapping detected",
            "T4": "Route withdrawals cascade",
            "T5": "Prefix reachability loss",
        },
        "correlation": {
            "incident_title": "BGP Hold-Timer Mismatch on Juniper Edge",
            "root_device": "edge-router",
            "recommendation": "Restore hold-time 90 or align with upstream peer.",
        },
        "correlation_rules": [{"id": "junos-bgp-hold-mismatch", "pattern": "junos_bgp_hold_mismatch"}],
        "devices": devices,
    }


def attach_topology(scenario: dict) -> dict:
    presets_path = os.path.join(PKG, "topology-presets.json")
    if os.path.isfile(presets_path):
        with open(presets_path, encoding="utf-8") as f:
            presets = json.load(f)
        if scenario["id"] in presets:
            scenario["topology"] = presets[scenario["id"]]
    return scenario


def main():
    scenarios = [
        build_acl_regression(),
        build_ospf(),
        build_bgp(),
        build_stp(),
        build_juniper(),
        build_juniper_isis(),
        build_juniper_rsvp(),
        build_juniper_policer(),
        build_nokia(),
        build_nokia_sdp(),
        build_nokia_vprn(),
        build_nokia_qos(),
    ]
    for sc in scenarios:
        sc = attach_topology(sc)
        path = os.path.join(PKG, f"{sc['id']}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(sc, f, indent=2)
        print("wrote", path)
    print("done")


if __name__ == "__main__":
    main()
