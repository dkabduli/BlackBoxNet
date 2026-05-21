from pydantic import BaseModel
from typing import Any


class RunStepRequest(BaseModel):
    auto_advance: bool = True
    scenario_id: str | None = None


class RunStepResponse(BaseModel):
    current_time: int
    time_step: str
    devices_collected: int
    snapshots_created: int
    events_generated: list[dict[str, Any]] = []
    incidents_created: int = 0
    git_commits: int = 0


class ResetResponse(BaseModel):
    status: str
    current_time: int
    message: str


class SimulationStatusDevice(BaseModel):
    device_id: str
    hostname: str
    current_state: str


class SimulationProgress(BaseModel):
    percentage: int
    next_step: str | None
    can_advance: bool
    can_run_current_step: bool
    has_current_step_data: bool
    is_complete: bool


class SimulationStatusResponse(BaseModel):
    current_time: int
    current_step: str
    total_steps: int
    scenario_name: str
    scenario_id: str
    devices: list[SimulationStatusDevice] = []
    progress: SimulationProgress
