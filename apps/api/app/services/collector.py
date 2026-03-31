import hashlib
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.scenario_engine import ScenarioEngine, DeviceState
from app.models.device import Device
from app.models.config import ConfigVersion
from app.models.event import Event
from app.services.snapshot_processor import SnapshotProcessor
from app.services.config_git import ConfigGitService
from app.services.diff_engine import DiffEngine
from app.services.event_engine import EventEngine
from app.services.correlation_engine import CorrelationEngine


class CollectorService:
    def __init__(
        self,
        scenario_engine: ScenarioEngine,
        db: AsyncSession,
        config_git: ConfigGitService,
    ):
        self._scenario = scenario_engine
        self._db = db
        self._config_git = config_git
        self._snapshot_processor = SnapshotProcessor(db)
        self._diff_engine = DiffEngine(db)
        self._event_engine = EventEngine(db)
        self._correlation_engine = CorrelationEngine(db)

    async def _ensure_devices_exist(self) -> dict[str, uuid.UUID]:
        """Create device records if they don't exist, return hostname->id map."""
        device_map: dict[str, uuid.UUID] = {}
        current_time = self._scenario.get_current_time()

        for device_id in self._scenario.get_device_ids():
            state = self._scenario.get_device_state(device_id, current_time)
            result = await self._db.execute(
                select(Device).where(Device.hostname == state.hostname)
            )
            device = result.scalar_one_or_none()

            if device is None:
                device = Device(
                    hostname=state.hostname,
                    management_ip=state.management_ip,
                    vendor=state.vendor,
                    role=state.role,
                    metadata_={"scenario_device_id": state.device_id},
                )
                self._db.add(device)
                await self._db.flush()

            device_map[state.hostname] = device.id

        return device_map

    async def collect_all_devices(self) -> dict[str, Any]:
        current_time = self._scenario.get_current_time()
        base_timestamp = datetime.now(timezone.utc)
        scenario_offset = timedelta(seconds=current_time)
        timestamp = base_timestamp

        device_map = await self._ensure_devices_exist()
        all_states = self._scenario.get_all_devices_state(current_time)
        scenario_info = self._scenario.get_scenario_info()

        snapshots_created = []
        all_events = []
        config_changed_devices: list[str] = []
        git_commits = 0

        for device_state in all_states:
            device_id = device_map[device_state.hostname]
            config_content = self._scenario.get_config_content(device_state.config_path)
            config_hash = hashlib.sha256(config_content.encode()).hexdigest()

            previous_snapshot = await self._snapshot_processor.get_previous_snapshot(device_id)

            snapshot = await self._snapshot_processor.persist_snapshot(
                device_state, device_id, config_hash, timestamp
            )
            snapshots_created.append(snapshot)

            loaded_snapshot = await self._snapshot_processor.get_snapshot_with_interfaces(snapshot.id)

            config_changed = previous_snapshot is None or config_hash != previous_snapshot.config_hash

            if config_changed:
                config_changed_devices.append(device_state.hostname)
                rel_path = self._config_git.write_config(
                    device_state.hostname, config_content, timestamp
                )

            prev_interfaces = previous_snapshot.interface_snapshots if previous_snapshot else None
            events = await self._event_engine.detect_events(
                loaded_snapshot,
                previous_snapshot,
                loaded_snapshot.interface_snapshots,
                prev_interfaces,
            )
            all_events.extend(events)

        if config_changed_devices:
            commit_hash = self._config_git.commit_changes(timestamp, config_changed_devices)
            git_commits = 1

            for device_state in all_states:
                if device_state.hostname in config_changed_devices:
                    device_id = device_map[device_state.hostname]
                    config_content = self._scenario.get_config_content(device_state.config_path)
                    config_hash = hashlib.sha256(config_content.encode()).hexdigest()

                    cv = ConfigVersion(
                        device_id=device_id,
                        timestamp=timestamp,
                        git_commit_hash=commit_hash,
                        config_hash=config_hash,
                        config_path=f"{device_state.hostname}/{timestamp.strftime('%Y-%m-%dT%H-%M-%S')}.cfg",
                        config_size_bytes=len(config_content),
                    )
                    self._db.add(cv)
                    await self._db.flush()

                    previous_snapshot = None
                    result = await self._db.execute(
                        select(ConfigVersion)
                        .where(ConfigVersion.device_id == device_id)
                        .where(ConfigVersion.id != cv.id)
                        .order_by(ConfigVersion.timestamp.desc())
                        .limit(1)
                    )
                    prev_cv = result.scalar_one_or_none()

                    if prev_cv:
                        old_content = self._config_git.get_config_at_commit(
                            device_state.hostname, prev_cv.git_commit_hash
                        )
                        if old_content:
                            diff = await self._diff_engine.generate_diff(
                                old_content, config_content,
                                device_id, timestamp, prev_cv, cv,
                            )
                            for evt in all_events:
                                if (evt.device_id == device_id
                                        and evt.event_type == "CONFIG_CHANGE"):
                                    evt.related_config_diff_id = diff.id
                                    evt.description = self._build_config_change_desc(diff)
                                    await self._db.flush()

        outage_events = [e for e in all_events if e.event_type == "OUTAGE_STARTED"]
        incidents_created = 0
        if outage_events:
            all_stored_events_result = await self._db.execute(
                select(Event).order_by(Event.timestamp)
            )
            all_stored_events = list(all_stored_events_result.scalars().all())

            incident = await self._correlation_engine.create_incident_from_outage(
                outage_events[0],
                all_stored_events,
                device_map,
                scenario_info.get("affected_subnet", "10.0.1.0/24"),
            )
            incidents_created = 1

        await self._db.commit()

        step_names = {0: "T1", 60: "T2", 120: "T3", 180: "T4", 240: "T5"}

        return {
            "current_time": current_time,
            "time_step": step_names.get(current_time, f"T{self._scenario.get_current_step_index() + 1}"),
            "devices_collected": len(all_states),
            "snapshots_created": len(snapshots_created),
            "events_generated": [
                {
                    "event_id": str(e.id),
                    "event_type": e.event_type,
                    "device_id": str(e.device_id),
                    "severity": e.severity,
                    "title": e.title,
                }
                for e in all_events
            ],
            "incidents_created": incidents_created,
            "git_commits": git_commits,
        }

    def _build_config_change_desc(self, diff) -> str:
        if diff.semantic_summary:
            parts = []
            for s in diff.semantic_summary:
                if s.get("change_type") == "ACL_MODIFIED":
                    parts.append(f"ACL {s.get('entity', '')} {s.get('action', '')}")
                elif s.get("change_type") == "INTERFACE_ACL_BINDING":
                    parts.append(f"ACL binding changed on {s.get('entity', '')}")
            if parts:
                return "; ".join(parts)
        return "Configuration changed"
