from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Any


class RootDeviceSchema(BaseModel):
    id: UUID
    hostname: str
    vendor: str | None = None
    role: str | None = None

    model_config = {"from_attributes": True}


class AffectedDeviceSchema(BaseModel):
    device_id: UUID
    hostname: str
    impact_level: str

    model_config = {"from_attributes": True}


class IncidentListItem(BaseModel):
    id: UUID
    title: str
    start_time: datetime
    end_time: datetime | None = None
    status: str
    affected_scope: str | None = None
    root_device: RootDeviceSchema | None = None
    summary: str | None = None
    suspicion_summary: str | None = None
    event_count: int = 0
    affected_device_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class TimelineEventSchema(BaseModel):
    id: UUID
    device_id: UUID
    device_hostname: str
    timestamp: datetime
    event_type: str
    severity: str
    title: str
    description: str | None = None
    config_diff: dict[str, Any] | None = None
    is_primary_cause: bool = False
    relevance_score: float = 1.0
    metadata: dict[str, Any] = {}

    model_config = {"from_attributes": True}


class TimelineResponse(BaseModel):
    incident_id: UUID
    events: list[TimelineEventSchema]
    meta: dict[str, Any] = {}


class CorrelationResponse(BaseModel):
    incident_id: str
    suspicion_summary: str | None = None
    primary_suspect: dict[str, Any] | None = None
    correlation_flags: list[dict[str, Any]] = []
    recommendation: str | None = None
    timeline_analysis: dict[str, Any] = {}


class IncidentDetail(IncidentListItem):
    affected_devices: list[AffectedDeviceSchema] = []
    event_summary: dict[str, Any] = {}
