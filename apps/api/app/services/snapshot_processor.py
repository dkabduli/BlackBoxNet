import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.scenario_engine import DeviceState, InterfaceState
from app.models.snapshot import Snapshot, InterfaceSnapshot


class SnapshotProcessor:
    def __init__(self, db: AsyncSession):
        self._db = db

    async def persist_snapshot(
        self, device_state: DeviceState, device_id: uuid.UUID, config_hash: str, timestamp: datetime
    ) -> Snapshot:
        snapshot = Snapshot(
            device_id=device_id,
            timestamp=timestamp,
            config_hash=config_hash,
            cpu_usage=device_state.cpu_usage,
            memory_usage=device_state.memory_usage,
            latency_ms=device_state.latency_ms,
            packet_loss_pct=device_state.packet_loss_pct,
            snapshot_source="simulation",
            tags=device_state.tags,
            metadata_={"scenario_timestamp": device_state.timestamp},
        )
        self._db.add(snapshot)
        await self._db.flush()

        for iface in device_state.interfaces:
            ip_addr = None
            if iface.ip_address:
                ip_addr = iface.ip_address.split("/")[0] if "/" in iface.ip_address else iface.ip_address

            iface_snapshot = InterfaceSnapshot(
                snapshot_id=snapshot.id,
                interface_name=iface.name,
                admin_state=iface.admin_state,
                oper_state=iface.oper_state,
                rx_errors=iface.rx_errors,
                tx_errors=iface.tx_errors,
                description=iface.description,
                ip_address=ip_addr,
                speed_mbps=1000,
                duplex="full",
            )
            self._db.add(iface_snapshot)

        await self._db.flush()
        return snapshot

    async def get_previous_snapshot(self, device_id: uuid.UUID) -> Snapshot | None:
        result = await self._db.execute(
            select(Snapshot)
            .where(Snapshot.device_id == device_id)
            .order_by(Snapshot.timestamp.desc())
            .limit(1)
            .options(selectinload(Snapshot.interface_snapshots))
        )
        return result.scalar_one_or_none()

    async def get_snapshot_with_interfaces(self, snapshot_id: uuid.UUID) -> Snapshot | None:
        result = await self._db.execute(
            select(Snapshot)
            .where(Snapshot.id == snapshot_id)
            .options(selectinload(Snapshot.interface_snapshots))
        )
        return result.scalar_one_or_none()
