import uuid
from datetime import datetime, timezone

import pytest

from app.models.event import Event
from app.models.incident import IncidentAffectedDevice, IncidentEvent
from app.services.correlation_engine import CorrelationEngine, CorrelationFlag


class FakeAsyncSession:
    def __init__(self) -> None:
        self.added: list[object] = []

    def add(self, obj: object) -> None:
        if getattr(obj, "id", None) is None:
            setattr(obj, "id", uuid.uuid4())
        self.added.append(obj)

    async def flush(self) -> None:
        return None


@pytest.mark.asyncio
async def test_create_incident_from_outage_sets_summary_and_relationships(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeAsyncSession()
    engine = CorrelationEngine(db)  # type: ignore[arg-type]
    ts = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    edge_id = uuid.uuid4()
    dist_id = uuid.uuid4()
    access_id = uuid.uuid4()

    config_change = Event(
        id=uuid.uuid4(),
        scenario_id="acl-regression",
        device_id=edge_id,
        timestamp=ts,
        event_type="CONFIG_CHANGE",
        severity="WARNING",
        title="ACL updated",
        description="ACL modified",
        metadata_={},
    )
    outage = Event(
        id=uuid.uuid4(),
        scenario_id="acl-regression",
        device_id=access_id,
        timestamp=ts,
        event_type="OUTAGE_STARTED",
        severity="CRITICAL",
        title="Outage started",
        description="Subnet unreachable",
        metadata_={},
    )

    async def fake_apply_rules(*_args, **_kwargs) -> list[CorrelationFlag]:
        return [
            CorrelationFlag(
                rule="acl_deny_affects_subnet",
                suspicion_level="high",
                description="New ACL deny rule matches affected subnet",
                evidence={"affected_subnet": "10.0.1.0/24"},
            )
        ]

    monkeypatch.setattr(engine, "_apply_rules", fake_apply_rules)

    incident = await engine.create_incident_from_outage(
        outage,
        [config_change, outage],
        {
            "edge-router-1": edge_id,
            "dist-switch-1": dist_id,
            "access-switch-1": access_id,
        },
        "acl-regression",
        {
            "incident_title": "ACL Regression Blocks Downstream Subnet",
            "root_device": "edge-router-1",
        },
        [{"id": "acl-deny-subnet", "pattern": "acl_deny_subnet"}],
        "10.0.1.0/24",
    )

    assert incident.root_device_id == edge_id
    assert incident.title == "ACL Regression Blocks Downstream Subnet"
    assert "10.0.1.0/24" in (incident.suspicion_summary or "")

    incident_events = [obj for obj in db.added if isinstance(obj, IncidentEvent)]
    affected_devices = [obj for obj in db.added if isinstance(obj, IncidentAffectedDevice)]

    assert len(incident_events) == 2
    assert len(affected_devices) == 3
    assert any(event.is_primary_cause for event in incident_events)
