import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.event import Event
from app.models.incident import Incident, IncidentEvent, IncidentAffectedDevice
from app.models.config import ConfigDiff
from app.models.device import Device


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
        affected_subnet: str = "10.0.1.0/24",
    ) -> Incident:
        root_device_id = device_map.get("edge-router-1")

        incident = Incident(
            title="ACL Regression Blocks Downstream Subnet",
            start_time=outage_event.timestamp,
            status="active",
            affected_scope=f"subnet {affected_subnet}, devices: access-switch-1, dist-switch-1",
            root_device_id=root_device_id,
            summary=f"Complete connectivity loss for subnet {affected_subnet}",
        )
        self._db.add(incident)
        await self._db.flush()

        for i, event in enumerate(all_events):
            is_primary = event.event_type == "CONFIG_CHANGE"
            relevance = 1.0 if is_primary or event.event_type == "OUTAGE_STARTED" else 0.8
            ie = IncidentEvent(
                incident_id=incident.id,
                event_id=event.id,
                relevance_score=relevance,
                is_primary_cause=is_primary,
            )
            self._db.add(ie)

        impact_map = {
            "edge-router-1": "critical",
            "dist-switch-1": "high",
            "access-switch-1": "critical",
        }
        for hostname, dev_id in device_map.items():
            iad = IncidentAffectedDevice(
                incident_id=incident.id,
                device_id=dev_id,
                impact_level=impact_map.get(hostname, "medium"),
            )
            self._db.add(iad)

        await self._db.flush()

        flags = await self._apply_rules(incident, all_events)
        suspicion_summary = self._generate_suspicion_summary(flags, all_events)
        incident.suspicion_summary = suspicion_summary
        await self._db.flush()

        return incident

    async def _apply_rules(
        self, incident: Incident, events: list[Event]
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
            if cc.related_config_diff_id:
                result = await self._db.execute(
                    select(ConfigDiff).where(ConfigDiff.id == cc.related_config_diff_id)
                )
                diff = result.scalar_one_or_none()
                if diff and diff.semantic_summary:
                    for sem in diff.semantic_summary:
                        if sem.get("change_type") == "ACL_MODIFIED":
                            denied = sem.get("details", {}).get("denied_subnet")
                            if denied and "10.0.1.0" in denied:
                                flags.append(
                                    CorrelationFlag(
                                        rule="acl_deny_affects_subnet",
                                        suspicion_level="high",
                                        description="New ACL deny rule matches affected subnet",
                                        evidence={
                                            "denied_subnet": denied,
                                            "affected_subnet": "10.0.1.0/24",
                                            "acl_name": sem.get("entity", ""),
                                            "deny_rule": sem.get("details", {}).get("rules", [""])[0],
                                        },
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
        self, flags: list[CorrelationFlag], events: list[Event]
    ) -> str:
        config_changes = [e for e in events if e.event_type == "CONFIG_CHANGE"]
        if not config_changes:
            return "No config changes found before outage."

        cc = config_changes[0]
        ts = cc.timestamp.strftime("%H:%M:%SZ")

        for f in flags:
            if f.rule == "acl_deny_affects_subnet":
                subnet = f.evidence.get("affected_subnet", "unknown")
                return (
                    f"ACL change on edge-router-1 at {ts} preceded latency spike and outage. "
                    f"New deny rule blocks traffic from affected subnet {subnet}."
                )

        return (
            f"Config change on edge-router-1 at {ts} preceded degradation events. "
            f"This change is the primary suspect for the observed outage."
        )

    async def get_correlation_data(
        self, incident_id: uuid.UUID
    ) -> dict[str, Any]:
        result = await self._db.execute(
            select(Incident).where(Incident.id == incident_id)
        )
        incident = result.scalar_one_or_none()
        if not incident:
            return {}

        ie_result = await self._db.execute(
            select(IncidentEvent)
            .where(IncidentEvent.incident_id == incident_id)
        )
        incident_events = ie_result.scalars().all()

        event_ids = [ie.event_id for ie in incident_events]
        events_result = await self._db.execute(
            select(Event).where(Event.id.in_(event_ids)).order_by(Event.timestamp)
        )
        events = events_result.scalars().all()

        flags = await self._apply_rules(incident, list(events))

        primary_ie = next((ie for ie in incident_events if ie.is_primary_cause), None)
        primary_event = None
        if primary_ie:
            primary_event = next((e for e in events if e.id == primary_ie.event_id), None)

        return {
            "incident_id": str(incident.id),
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
            "recommendation": (
                "Review and rollback ACL change on edge-router-1. "
                "The deny rule for 10.0.1.0/24 should be removed or "
                "reordered after the permit statement."
            ),
        }
