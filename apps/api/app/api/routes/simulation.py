from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.simulation import RunStepRequest, RunStepResponse, ResetResponse, SimulationStatusResponse

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


@router.post("/run-step")
async def run_step(
    body: RunStepRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    from app.main import get_scenario_engine, get_config_git_service
    from app.services.collector import CollectorService

    scenario = get_scenario_engine()
    config_git = get_config_git_service()

    collector = CollectorService(scenario, db, config_git)
    result = await collector.collect_all_devices()
    scenario.mark_current_step_collected()

    if body is None or body.auto_advance:
        scenario.advance_time()

    return {"data": result, "meta": {}}


@router.post("/reset")
async def reset_simulation(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    from app.main import get_scenario_engine, get_config_git_service
    from app.models.incident import IncidentAffectedDevice, IncidentEvent, Incident
    from app.models.event import Event
    from app.models.config import ConfigDiff, ConfigVersion
    from app.models.snapshot import InterfaceSnapshot, Snapshot
    from app.models.device import Device

    await db.execute(delete(IncidentAffectedDevice))
    await db.execute(delete(IncidentEvent))
    await db.execute(delete(Incident))
    await db.execute(delete(Event))
    await db.execute(delete(ConfigDiff))
    await db.execute(delete(ConfigVersion))
    await db.execute(delete(InterfaceSnapshot))
    await db.execute(delete(Snapshot))
    await db.execute(delete(Device))
    await db.commit()

    scenario = get_scenario_engine()
    scenario.reset()

    config_git = get_config_git_service()
    config_git.cleanup()

    return {
        "data": {
            "status": "reset",
            "current_time": 0,
            "message": "Simulation reset to T1 (healthy baseline)",
        }
    }


@router.get("/status")
async def get_status() -> dict[str, Any]:
    from app.main import get_scenario_engine

    scenario = get_scenario_engine()
    info = scenario.get_scenario_info()
    current_time = scenario.get_current_time()
    step_index = scenario.get_current_step_index()
    total_steps = scenario.get_total_steps()
    time_steps = scenario.get_time_steps()
    has_current_step_data = scenario.has_current_step_data()
    can_run_current_step = scenario.can_run_current_step()
    is_complete = scenario.is_complete()

    step_names = {0: "T1", 60: "T2", 120: "T3", 180: "T4", 240: "T5"}
    current_step = step_names.get(current_time, f"T{step_index + 1}")

    next_step = None
    if can_run_current_step:
        next_step = current_step
    elif step_index + 1 < total_steps:
        next_time = time_steps[step_index + 1]
        next_step = step_names.get(next_time, f"T{step_index + 2}")

    progress_index = step_index
    if step_index == total_steps - 1 and not has_current_step_data:
        progress_index = max(step_index - 1, 0)
    percentage = int((progress_index / max(total_steps - 1, 1)) * 100)

    devices = []
    for did in scenario.get_device_ids():
        try:
            state = scenario.get_device_state(did, current_time)
            pkt_loss = state.packet_loss_pct or 0
            if pkt_loss >= 80:
                status = "critical"
            elif pkt_loss >= 5 or (state.latency_ms and state.latency_ms >= 50):
                status = "degraded"
            else:
                status = "healthy"
            devices.append({
                "device_id": did,
                "hostname": state.hostname,
                "current_state": status,
            })
        except Exception:
            pass

    return {
        "data": {
            "current_time": current_time,
            "current_step": current_step,
            "total_steps": total_steps,
            "scenario_name": info["name"],
            "scenario_id": info["scenario_id"],
            "devices": devices,
            "progress": {
                "percentage": percentage,
                "next_step": next_step,
                "can_advance": scenario.can_advance(),
                "can_run_current_step": can_run_current_step,
                "has_current_step_data": has_current_step_data,
                "is_complete": is_complete,
            },
        }
    }
