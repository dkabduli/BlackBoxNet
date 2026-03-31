from datetime import datetime
from uuid import UUID
from pydantic import BaseModel
from typing import Any


class ConfigVersionSchema(BaseModel):
    id: UUID
    device_id: UUID
    timestamp: datetime
    git_commit_hash: str
    config_hash: str
    config_path: str
    config_size_bytes: int | None = None

    model_config = {"from_attributes": True}


class SemanticChangeSchema(BaseModel):
    change_type: str
    entity: str
    action: str
    details: dict[str, Any] = {}
    suspicion_level: str
    reason: str


class ConfigDiffVersionSchema(BaseModel):
    id: UUID
    timestamp: datetime
    git_commit_hash: str


class ConfigDiffResponse(BaseModel):
    id: UUID
    device_id: UUID
    device_hostname: str | None = None
    timestamp: datetime
    previous_version: ConfigDiffVersionSchema | None = None
    current_version: ConfigDiffVersionSchema | None = None
    diff_text: str
    lines_added: int
    lines_removed: int
    lines_changed: int
    semantic_summary: list[dict[str, Any]] = []
    suspicion_level: str
    summary: str | None = None

    model_config = {"from_attributes": True}


class ConfigContentResponse(BaseModel):
    device_id: UUID
    hostname: str | None = None
    version_id: UUID | None = None
    timestamp: datetime | None = None
    git_commit_hash: str | None = None
    content: str
