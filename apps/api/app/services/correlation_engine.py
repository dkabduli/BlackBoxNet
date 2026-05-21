import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.incident import Incident, IncidentEvent, IncidentAffectedDevice
from app.models.config import ConfigDiff


@dataclass
class CorrelationFlag:
    rule: str
    suspicion_level: str
    description: str
    evidence: dict[str, Any]


class CorrelationEngine:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def create_incident_from_outage(
        self,
        outage_event: Event,
        all_events: list[Event],
        device_map: dict[str, uuid.UUID],
        scenario_id: str,
        correlation_config: dict[str, Any],
        correlation_rules: list[dict[str, Any]],
        affected_subnet: str = "10.0.1.0/24",
    ) -> Incident:
        root_hostname = correlation_config.get("root_device", "edge-router-1")
        root_device_id = device_map.get(root_hostname)
        title = correlation_config.get("incident_title", "Network Outage Detected")
        scope_devices = ", ".join(sorted(device_map.keys()))

        incident = Incident(
            scenario_id=scenario_id,
            title=title,
            start_time=outage_event.timestamp,
            status="active",
            affected_scope=f"subnet {affected_subnet}, devices: {scope_devices}",
            root_device_id=root_device_id,
            summary=f"Complete connectivity loss for subnet {affected_subnet}",
        )
        self._db.add(incident)
        await self._db.flush()

        for event in all_events:
            is_primary = event.event_type == "CONFIG_CHANGE"
            relevance = 1.0 if is_primary or event.event_type == "OUTAGE_STARTED" else 0.8
            self._db.add(
                IncidentEvent(
                    incident_id=incident.id,
                    event_id=event.id,
                    relevance_score=relevance,
                    is_primary_cause=is_primary,
                )
            )

        impact_map = correlation_config.get("impact_map") or {
            h: "high" for h in device_map
        }
        for hostname, dev_id in device_map.items():
            self._db.add(
                IncidentAffectedDevice(
                    incident_id=incident.id,
                    device_id=dev_id,
                    impact_level=impact_map.get(hostname, "medium"),
                )
            )

        await self._db.flush()

        flags = await self._apply_rules(
            incident, all_events, correlation_rules, affected_subnet, root_hostname
        )
        incident.suspicion_summary = self._generate_suspicion_summary(
            flags, all_events, root_hostname, correlation_config
        )
        await self._db.flush()
        return incident

    async def _apply_rules(
        self,
        incident: Incident,
        events: list[Event],
        correlation_rules: list[dict[str, Any]],
        affected_subnet: str,
        root_hostname: str,
    ) -> list[CorrelationFlag]:
        flags: list[CorrelationFlag] = []
        config_changes = [e for e in events if e.event_type == "CONFIG_CHANGE"]
        degradation_events = [
            e for e in events
            if e.event_type in ("LATENCY_SPIKE", "PACKET_LOSS_INCREASE")
        ]

        for cc in config_changes:
            for deg in degradation_events:
                if deg.timestamp > cc.timestamp:
                    delta = (deg.timestamp - cc.timestamp).total_seconds()
                    if delta <= 300:
                        flags.append(
                            CorrelationFlag(
                                rule="recent_config_change_before_degradation",
                                suspicion_level="high",
                                description=f"Config change occurred {int(delta)}s before first degradation event",
                                evidence={
                                    "config_change_time": cc.timestamp.isoformat(),
                                    "first_degradation_time": deg.timestamp.isoformat(),
                                    "time_delta_seconds": int(delta),
                                },
                            )
                        )
                        break

        for cc in config_changes:
            if not cc.related_config_diff_id:
                continue
            result = await self._db.execute(
                select(ConfigDiff).where(ConfigDiff.id == cc.related_config_diff_id)
            )
            diff = result.scalar_one_or_none()
            if not diff or not diff.semantic_summary:
                continue

            for sem in diff.semantic_summary:
                change_type = sem.get("change_type", "")
                if change_type == "ACL_MODIFIED":
                    denied = sem.get("details", {}).get("denied_subnet")
                    if denied and affected_subnet.split("/")[0] in denied:
                        flags.append(
                            CorrelationFlag(
                                rule="acl_deny_affects_subnet",
                                suspicion_level="high",
                                description="New ACL deny rule matches affected subnet",
                                evidence={
                                    "denied_subnet": denied,
                                    "affected_subnet": affected_subnet,
                                    "acl_name": sem.get("entity", ""),
                                },
                            )
                        )
                elif change_type == "OSPF_TIMER_MISMATCH":
                    flags.append(
                        CorrelationFlag(
                            rule="ospf-timer-mismatch",
                            suspicion_level="high",
                            description=sem.get("reason", "OSPF hello/dead timer mismatch"),
                            evidence=sem.get("details", {}),
                        )
                    )
                elif change_type == "LDP_LABEL_COLLISION":
                    flags.append(
                        CorrelationFlag(
                            rule="ldp-label-collision",
                            suspicion_level="critical",
                            description=sem.get("reason", "LDP label collision"),
                            evidence=sem.get("details", {}),
                        )
                    )
                elif change_type == "BGP_COMMUNITY_STRIPPED":
                    flags.append(
                        CorrelationFlag(
                            rule="bgp-community-stripped",
                            suspicion_level="critical",
                            description=sem.get("reason", "BGP community stripped"),
                            evidence=sem.get("details", {}),
                        )
                    )
                elif change_type == "JUNOS_BGP_HOLD_MISMATCH":
                    flags.append(
                        CorrelationFlag(
                            rule="junos-bgp-hold-mismatch",
                            suspicion_level="critical",
                            description=sem.get("reason", "BGP hold-time mismatch"),
                            evidence=sem.get("details", {}),
                        )
                    )
                elif change_type == "STP_PRIORITY_SUBVERSION":
                    flags.append(
                        CorrelationFlag(
                            rule="stp-priority-subversion",
                            suspicion_level="critical",
                            description=sem.get("reason", "STP priority subversion"),
                            evidence=sem.get("details", {}),
                        )
                    )

        for rule in correlation_rules:
            pattern = rule.get("pattern", "")
            if pattern and not any(f.rule == rule.get("id", pattern) for f in flags):
                if pattern in ("ospf_timer_mismatch", "ldp_label_collision", "bgp_community_stripped", "stp_priority_subversion", "acl_deny_subnet"):
                    flags.append(
                        CorrelationFlag(
                            rule=rule.get("id", pattern),
                            suspicion_level="high",
                            description=rule.get("message", f"Correlation rule {pattern}"),
                            evidence={"suspect_device": rule.get("suspect_device", root_hostname)},
                        )
                    )

        if config_changes:
            first_change = min(config_changes, key=lambda e: e.timestamp)
            non_config = [e for e in events if e.event_type != "CONFIG_CHANGE"]
            if non_config:
                next_event = min(non_config, key=lambda e: e.timestamp)
                if first_change.timestamp <= next_event.timestamp:
                    flags.append(
                        CorrelationFlag(
                            rule="time_ordered_primary_suspect",
                            suspicion_level="high",
                            description="Config change is chronologically first event",
                            evidence={
                                "config_change_time": first_change.timestamp.isoformat(),
                                "next_event_time": next_event.timestamp.isoformat(),
                            },
                        )
                    )

        return flags

    def _generate_suspicion_summary(
        self,
        flags: list[CorrelationFlag],
        events: list[Event],
        root_hostname: str,
        correlation_config: dict[str, Any],
    ) -> str:
        config_changes = [e for e in events if e.event_type == "CONFIG_CHANGE"]
        if not config_changes:
            return "No config changes found before outage."

        ts = config_changes[0].timestamp.strftime("%H:%M:%SZ")
        for f in flags:
            if f.rule == "acl_deny_affects_subnet":
                subnet = f.evidence.get("affected_subnet", "unknown")
                return (
                    f"ACL change on {root_hostname} at {ts} preceded latency spike and outage. "
                    f"New deny rule blocks traffic from {subnet}."
                )
            if f.rule == "ospf-timer-mismatch":
                return (
                    f"OSPF timer change on {root_hostname} at {ts} caused adjacency flaps "
                    "and area partition."
                )
            if f.rule == "ldp-label-collision":
                return (
                    f"Static label map on {root_hostname} at {ts} silently overwrote LFIB "
                    "entry 131071 for 10.0.1.0/24."
                )
            if f.rule == "bgp-community-stripped":
                return (
                    f"route-map change on {root_hostname} at {ts} leaked internal prefixes "
                    "to upstream."
                )
            if f.rule == "junos-bgp-hold-mismatch":
                return (
                    f"BGP hold-time change on {root_hostname} at {ts} caused session "
                    "flaps and route withdrawal."
                )
            if f.rule == "stp-priority-subversion":
                return (
                    f"STP priority change on {root_hostname} at {ts} triggered root "
                    "re-election and TCN storm."
                )

        default_msg = correlation_config.get(
            "suspicion_template",
            f"Config change on {root_hostname} at {ts} preceded degradation events.",
        )
        return default_msg

    async def get_correlation_data(self, incident_id: uuid.UUID) -> dict[str, Any]:
        result = await self._db.execute(
            select(Incident).where(Incident.id == incident_id)
        )
        incident = result.scalar_one_or_none()
        if not incident:
            return {}

        ie_result = await self._db.execute(
            select(IncidentEvent).where(IncidentEvent.incident_id == incident_id)
        )
        incident_events = ie_result.scalars().all()
        event_ids = [ie.event_id for ie in incident_events]
        events_result = await self._db.execute(
            select(Event).where(Event.id.in_(event_ids)).order_by(Event.timestamp)
        )
        events = events_result.scalars().all()

        correlation_rules: list[dict[str, Any]] = []
        affected_subnet = ""
        root_hostname = ""
        try:
            from app.main import get_scenario_manager

            engine = get_scenario_manager().get_engine(incident.scenario_id)
            correlation_rules = engine.get_correlation_rules()
            cfg = engine.get_correlation_config()
            root_hostname = cfg.get("root_device", "")
            affected_subnet = engine.get_scenario_info().get("affected_subnet", "") or ""
        except Exception:
            pass

        flags = await self._apply_rules(
            incident, list(events), correlation_rules, affected_subnet, root_hostname
        )

        primary_ie = next((ie for ie in incident_events if ie.is_primary_cause), None)
        primary_event = None
        if primary_ie:
            primary_event = next((e for e in events if e.id == primary_ie.event_id), None)

        return {
            "incident_id": str(incident.id),
            "scenario_id": incident.scenario_id,
            "suspicion_summary": incident.suspicion_summary,
            "primary_suspect": {
                "event_id": str(primary_event.id) if primary_event else None,
                "event_type": primary_event.event_type if primary_event else None,
                "device_id": str(primary_event.device_id) if primary_event else None,
                "timestamp": primary_event.timestamp.isoformat() if primary_event else None,
            } if primary_event else None,
            "correlation_flags": [
                {
                    "rule": f.rule,
                    "suspicion_level": f.suspicion_level,
                    "description": f.description,
                    "evidence": f.evidence,
                }
                for f in flags
            ],
            "recommendation": "Review root-cause config diff and rollback the suspect change.",
        }
