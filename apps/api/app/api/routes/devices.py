import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.models.device import Device
from app.models.snapshot import Snapshot, InterfaceSnapshot
from app.models.config import ConfigVersion
from app.schemas.device import (
    DeviceListItem, DeviceDetail, DeviceHealthResponse,
    HealthPoint, LatestSnapshotSchema, InterfaceSnapshotSchema,
    SnapshotSchema, ConfigVersionSchema,
)

router = APIRouter(prefix="/api/devices", tags=["devices"])


def compute_health_status(snapshot: Snapshot | None) -> str:
    if snapshot is None:
        return "unknown"
    pkt = float(snapshot.packet_loss_pct or 0)
    lat = float(snapshot.latency_ms or 0)
    cpu = float(snapshot.cpu_usage or 0)
    if pkt >= 80 or lat > 200 or cpu > 95:
        return "critical"
    if pkt >= 5 or lat >= 50 or cpu >= 80:
        return "degraded"
    return "healthy"


@router.get("")
async def list_devices(
    vendor: str | None = None,
    role: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    query = select(Device)
    if vendor:
        query = query.where(Device.vendor == vendor)
    if role:
        query = query.where(Device.role == role)

    count_result = await db.execute(select(func.count()).select_from(query.subquery()))
    total = count_result.scalar()

    query = query.offset(offset).limit(limit).order_by(Device.hostname)
    result = await db.execute(query)
    devices = result.scalars().all()

    items = []
    for device in devices:
        snap_result = await db.execute(
            select(Snapshot)
            .where(Snapshot.device_id == device.id)
            .order_by(Snapshot.timestamp.desc())
            .limit(1)
            .options(selectinload(Snapshot.interface_snapshots))
        )
        latest = snap_result.scalar_one_or_none()

        snapshot_data = None
        if latest:
            snapshot_data = LatestSnapshotSchema(
                id=latest.id,
                timestamp=latest.timestamp,
                config_hash=latest.config_hash,
                cpu_usage=float(latest.cpu_usage) if latest.cpu_usage else None,
                memory_usage=float(latest.memory_usage) if latest.memory_usage else None,
                latency_ms=float(latest.latency_ms) if latest.latency_ms else None,
                packet_loss_pct=float(latest.packet_loss_pct) if latest.packet_loss_pct else None,
                health_status=compute_health_status(latest),
                tags=latest.tags or [],
                interfaces=[
                    InterfaceSnapshotSchema(
                        name=i.interface_name,
                        admin_state=i.admin_state,
                        oper_state=i.oper_state,
                        rx_errors=i.rx_errors or 0,
                        tx_errors=i.tx_errors or 0,
                        description=i.description,
                        ip_address=str(i.ip_address) if i.ip_address else None,
                        speed_mbps=i.speed_mbps,
                    )
                    for i in latest.interface_snapshots
                ],
            )

        items.append(
            DeviceListItem(
                id=device.id,
                hostname=device.hostname,
                management_ip=str(device.management_ip),
                vendor=device.vendor,
                role=device.role,
                latest_snapshot=snapshot_data,
                metadata=device.metadata_ or {},
                created_at=device.created_at,
            )
        )

    return {
        "data": [item.model_dump() for item in items],
        "meta": {"total": total, "limit": limit, "offset": offset},
    }


@router.get("/{device_id}")
async def get_device(
    device_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    snap_result = await db.execute(
        select(Snapshot)
        .where(Snapshot.device_id == device.id)
        .order_by(Snapshot.timestamp.desc())
        .limit(1)
        .options(selectinload(Snapshot.interface_snapshots))
    )
    latest = snap_result.scalar_one_or_none()

    cv_result = await db.execute(
        select(ConfigVersion)
        .where(ConfigVersion.device_id == device.id)
        .order_by(ConfigVersion.timestamp.desc())
        .limit(1)
    )
    latest_cv = cv_result.scalar_one_or_none()

    snapshot_data = None
    if latest:
        snapshot_data = LatestSnapshotSchema(
            id=latest.id,
            timestamp=latest.timestamp,
            config_hash=latest.config_hash,
            cpu_usage=float(latest.cpu_usage) if latest.cpu_usage else None,
            memory_usage=float(latest.memory_usage) if latest.memory_usage else None,
            latency_ms=float(latest.latency_ms) if latest.latency_ms else None,
            packet_loss_pct=float(latest.packet_loss_pct) if latest.packet_loss_pct else None,
            health_status=compute_health_status(latest),
            tags=latest.tags or [],
            interfaces=[
                InterfaceSnapshotSchema(
                    name=i.interface_name,
                    admin_state=i.admin_state,
                    oper_state=i.oper_state,
                    rx_errors=i.rx_errors or 0,
                    tx_errors=i.tx_errors or 0,
                    description=i.description,
                    ip_address=str(i.ip_address) if i.ip_address else None,
                    speed_mbps=i.speed_mbps,
                )
                for i in latest.interface_snapshots
            ],
        )

    cv_data = None
    if latest_cv:
        cv_data = {"id": str(latest_cv.id), "timestamp": latest_cv.timestamp.isoformat(),
                    "git_commit_hash": latest_cv.git_commit_hash, "config_path": latest_cv.config_path}

    return {
        "data": {
            "id": str(device.id),
            "hostname": device.hostname,
            "management_ip": str(device.management_ip),
            "vendor": device.vendor,
            "role": device.role,
            "latest_snapshot": snapshot_data.model_dump() if snapshot_data else None,
            "latest_config_version": cv_data,
            "metadata": device.metadata_ or {},
            "created_at": device.created_at.isoformat(),
            "updated_at": device.updated_at.isoformat(),
        }
    }


@router.get("/{device_id}/health")
async def get_device_health(
    device_id: uuid.UUID,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    snap_result = await db.execute(
        select(Snapshot)
        .where(Snapshot.device_id == device_id)
        .order_by(Snapshot.timestamp.asc())
        .limit(limit)
    )
    snapshots = snap_result.scalars().all()

    time_series = [
        HealthPoint(
            timestamp=s.timestamp,
            cpu_usage=float(s.cpu_usage) if s.cpu_usage else None,
            memory_usage=float(s.memory_usage) if s.memory_usage else None,
            latency_ms=float(s.latency_ms) if s.latency_ms else None,
            packet_loss_pct=float(s.packet_loss_pct) if s.packet_loss_pct else None,
            tags=s.tags or [],
        )
        for s in snapshots
    ]

    return {
        "data": {
            "device_id": str(device_id),
            "hostname": device.hostname,
            "time_series": [t.model_dump() for t in time_series],
            "summary": {"data_points": len(time_series)},
        }
    }


@router.get("/{device_id}/snapshots")
async def get_device_snapshots(
    device_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    snap_result = await db.execute(
        select(Snapshot)
        .where(Snapshot.device_id == device_id)
        .order_by(Snapshot.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .options(selectinload(Snapshot.interface_snapshots))
    )
    snapshots = snap_result.scalars().all()

    return {
        "data": [
            {
                "id": str(s.id),
                "device_id": str(s.device_id),
                "timestamp": s.timestamp.isoformat(),
                "config_hash": s.config_hash,
                "cpu_usage": float(s.cpu_usage) if s.cpu_usage else None,
                "memory_usage": float(s.memory_usage) if s.memory_usage else None,
                "latency_ms": float(s.latency_ms) if s.latency_ms else None,
                "packet_loss_pct": float(s.packet_loss_pct) if s.packet_loss_pct else None,
                "snapshot_source": s.snapshot_source,
                "tags": s.tags or [],
                "interfaces": [
                    {
                        "name": i.interface_name,
                        "admin_state": i.admin_state,
                        "oper_state": i.oper_state,
                        "rx_errors": i.rx_errors or 0,
                        "tx_errors": i.tx_errors or 0,
                        "description": i.description,
                        "ip_address": str(i.ip_address) if i.ip_address else None,
                    }
                    for i in s.interface_snapshots
                ],
            }
            for s in snapshots
        ],
        "meta": {"total": len(snapshots), "limit": limit, "offset": offset},
    }
