from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Any


class InterfaceSnapshotSchema(BaseModel):
    name: str
    admin_state: str
    oper_state: str
    rx_errors: int = 0
    tx_errors: int = 0
    description: str | None = None
    ip_address: str | None = None
    speed_mbps: int | None = None

    model_config = {"from_attributes": True}


class LatestSnapshotSchema(BaseModel):
    id: UUID | None = None
    timestamp: datetime | None = None
    config_hash: str | None = None
    snapshot_source: str = "simulation"
    cpu_usage: float | None = None
    memory_usage: float | None = None
    latency_ms: float | None = None
    packet_loss_pct: float | None = None
    health_status: str = "healthy"
    interfaces: list[InterfaceSnapshotSchema] = []
    tags: list[str] = []

    model_config = {"from_attributes": True}


class DeviceListItem(BaseModel):
    id: UUID
    hostname: str
    management_ip: str
    vendor: str
    role: str
    latest_snapshot: LatestSnapshotSchema | None = None
    metadata: dict[str, Any] = {}
    created_at: datetime

    model_config = {"from_attributes": True}


class ConfigVersionSchema(BaseModel):
    id: UUID
    timestamp: datetime
    git_commit_hash: str
    config_path: str

    model_config = {"from_attributes": True}


class DeviceDetail(DeviceListItem):
    updated_at: datetime
    latest_config_version: ConfigVersionSchema | None = None


class HealthPoint(BaseModel):
    timestamp: datetime
    cpu_usage: float | None
    memory_usage: float | None
    latency_ms: float | None
    packet_loss_pct: float | None
    tags: list[str] = []


class DeviceHealthResponse(BaseModel):
    device_id: UUID
    hostname: str
    time_series: list[HealthPoint]
    summary: dict[str, Any] = {}


class SnapshotSchema(BaseModel):
    id: UUID
    device_id: UUID
    timestamp: datetime
    config_hash: str
    cpu_usage: float | None
    memory_usage: float | None
    latency_ms: float | None
    packet_loss_pct: float | None
    snapshot_source: str
    tags: list[str] = []
    interfaces: list[InterfaceSnapshotSchema] = []

    model_config = {"from_attributes": True}
