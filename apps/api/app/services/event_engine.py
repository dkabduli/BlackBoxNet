import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event import Event
from app.models.snapshot import Snapshot, InterfaceSnapshot


class EventEngine:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def detect_events(
        self,
        snapshot: Snapshot,
        previous: Snapshot | None,
        current_interfaces: list[InterfaceSnapshot],
        previous_interfaces: list[InterfaceSnapshot] | None,
    ) -> list[Event]:
        events: list[Event] = []

        if previous is None:
            return events

        if snapshot.config_hash != previous.config_hash:
            events.append(
                await self._emit_event(
                    device_id=snapshot.device_id,
                    timestamp=snapshot.timestamp,
                    event_type="CONFIG_CHANGE",
                    severity="INFO",
                    title="Configuration changed",
                    description=f"Config hash changed on device",
                    snapshot_id=snapshot.id,
                    metadata_={
                        "old_hash": previous.config_hash,
                        "new_hash": snapshot.config_hash,
                    },
                )
            )

        curr_latency = float(snapshot.latency_ms) if snapshot.latency_ms is not None else None
        prev_latency = float(previous.latency_ms) if previous.latency_ms is not None else None

        if curr_latency is not None and prev_latency is not None:
            if curr_latency > 50 and prev_latency < 30:
                events.append(
                    await self._emit_event(
                        device_id=snapshot.device_id,
                        timestamp=snapshot.timestamp,
                        event_type="LATENCY_SPIKE",
                        severity="WARNING",
                        title="Latency increased",
                        description=f"Latency spiked to {curr_latency}ms (baseline: {prev_latency}ms)",
                        snapshot_id=snapshot.id,
                        metadata_={
                            "baseline_latency": prev_latency,
                            "current_latency": curr_latency,
                            "threshold": 50.0,
                        },
                    )
                )

        curr_loss = float(snapshot.packet_loss_pct) if snapshot.packet_loss_pct is not None else 0
        prev_loss = float(previous.packet_loss_pct) if previous.packet_loss_pct is not None else 0

        if curr_loss > 20 and prev_loss < 10:
            events.append(
                await self._emit_event(
                    device_id=snapshot.device_id,
                    timestamp=snapshot.timestamp,
                    event_type="PACKET_LOSS_INCREASE",
                    severity="WARNING",
                    title="Packet loss detected",
                    description=f"Packet loss increased to {curr_loss}%",
                    snapshot_id=snapshot.id,
                    metadata_={
                        "baseline_packet_loss": prev_loss,
                        "current_packet_loss": curr_loss,
                    },
                )
            )

        curr_cpu = float(snapshot.cpu_usage) if snapshot.cpu_usage is not None else 0
        prev_cpu = float(previous.cpu_usage) if previous.cpu_usage is not None else 0

        if curr_cpu > 70 and prev_cpu < 40:
            events.append(
                await self._emit_event(
                    device_id=snapshot.device_id,
                    timestamp=snapshot.timestamp,
                    event_type="CPU_RISE",
                    severity="WARNING",
                    title="CPU utilization increased",
                    description=f"CPU at {curr_cpu}% (baseline: {prev_cpu}%)",
                    snapshot_id=snapshot.id,
                    metadata_={
                        "baseline_cpu": prev_cpu,
                        "current_cpu": curr_cpu,
                        "threshold": 70.0,
                    },
                )
            )

        if previous_interfaces and current_interfaces:
            prev_iface_map = {i.interface_name: i for i in previous_interfaces}
            for curr_iface in current_interfaces:
                prev_iface = prev_iface_map.get(curr_iface.interface_name)
                if prev_iface:
                    rx_delta = (curr_iface.rx_errors or 0) - (prev_iface.rx_errors or 0)
                    if rx_delta > 1000 or curr_iface.oper_state == "degraded":
                        events.append(
                            await self._emit_event(
                                device_id=snapshot.device_id,
                                timestamp=snapshot.timestamp,
                                event_type="INTERFACE_DEGRADED",
                                severity="ERROR",
                                title="Interface errors increased",
                                description=(
                                    f"{curr_iface.interface_name} rx_errors: {curr_iface.rx_errors}, "
                                    f"tx_errors: {curr_iface.tx_errors}"
                                ),
                                snapshot_id=snapshot.id,
                                metadata_={
                                    "interface": curr_iface.interface_name,
                                    "rx_errors": curr_iface.rx_errors,
                                    "tx_errors": curr_iface.tx_errors,
                                    "oper_state": curr_iface.oper_state,
                                },
                            )
                        )
                        break

        if curr_loss >= 80:
            events.append(
                await self._emit_event(
                    device_id=snapshot.device_id,
                    timestamp=snapshot.timestamp,
                    event_type="OUTAGE_STARTED",
                    severity="CRITICAL",
                    title="Outage detected",
                    description=f"Packet loss reached {curr_loss}%",
                    snapshot_id=snapshot.id,
                    metadata_={
                        "packet_loss": curr_loss,
                    },
                )
            )

        return events

    async def _emit_event(
        self,
        device_id: uuid.UUID,
        timestamp: datetime,
        event_type: str,
        severity: str,
        title: str,
        description: str,
        snapshot_id: uuid.UUID | None = None,
        config_diff_id: uuid.UUID | None = None,
        metadata_: dict[str, Any] | None = None,
    ) -> Event:
        event = Event(
            device_id=device_id,
            timestamp=timestamp,
            event_type=event_type,
            severity=severity,
            title=title,
            description=description,
            related_snapshot_id=snapshot_id,
            related_config_diff_id=config_diff_id,
            metadata_=metadata_ or {},
        )
        self._db.add(event)
        await self._db.flush()
        return event
