from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.simulation import RunStepRequest

router = APIRouter(prefix="/api/simulation", tags=["simulation"])


def _resolve_scenario_id(scenario_id: str | None) -> str:
    from app.main import get_scenario_manager

    manager = get_scenario_manager()
    sid = scenario_id or "acl-regression"
    if not manager.has_scenario(sid):
        raise HTTPException(status_code=404, detail=f"Unknown scenario_id: {sid}")
    return sid


async def _reset_scenario_data(
    scenario_id: str, db: AsyncSession, config_git, engine
) -> None:
    from app.models.incident import IncidentAffectedDevice, IncidentEvent, Incident
    from app.models.event import Event
    from app.models.config import ConfigDiff, ConfigVersion
    from app.models.snapshot import InterfaceSnapshot, Snapshot
    from app.models.device import Device

    device_result = await db.execute(
        select(Device.id).where(Device.scenario_id == scenario_id)
    )
    device_ids = [row[0] for row in device_result.all()]

    inc_result = await db.execute(
        select(Incident.id).where(Incident.scenario_id == scenario_id)
    )
    incident_ids = [row[0] for row in inc_result.all()]

    if incident_ids:
        await db.execute(
            delete(IncidentAffectedDevice).where(
                IncidentAffectedDevice.incident_id.in_(incident_ids)
            )
        )
        await db.execute(
            delete(IncidentEvent).where(IncidentEvent.incident_id.in_(incident_ids))
        )
        await db.execute(delete(Incident).where(Incident.scenario_id == scenario_id))
        await db.execute(delete(Event).where(Event.scenario_id == scenario_id))
        await db.execute(delete(ConfigDiff).where(ConfigDiff.scenario_id == scenario_id))
        await db.execute(delete(ConfigVersion).where(ConfigVersion.scenario_id == scenario_id))
        await db.execute(delete(InterfaceSnapshot).where(
            InterfaceSnapshot.snapshot_id.in_(
                select(Snapshot.id).where(Snapshot.scenario_id == scenario_id)
            )
        ))
        await db.execute(delete(Snapshot).where(Snapshot.scenario_id == scenario_id))
        await db.execute(delete(Device).where(Device.scenario_id == scenario_id))

    await db.commit()
    config_git.cleanup_scenario(scenario_id)
    engine.reset()


@router.post("/run-step")
async def run_step(
    body: RunStepRequest | None = None,
    scenario_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    from app.main import get_scenario_manager, get_config_git_service, get_ssh_config_fetcher
    from app.services.collector import CollectorService

    sid = _resolve_scenario_id(scenario_id)
    manager = get_scenario_manager()
    scenario = manager.get_engine(sid)
    config_git = get_config_git_service()
    ssh_fetcher = get_ssh_config_fetcher()

    collector = CollectorService(scenario, sid, db, config_git, ssh_fetcher)
    try:
        result = await collector.collect_all_devices()
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    scenario.mark_current_step_collected()
    if body is None or body.auto_advance:
        scenario.advance_time()

    return {"data": result, "meta": {}}


@router.post("/reset")
async def reset_simulation(
    scenario_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    from app.main import get_scenario_manager, get_config_git_service

    sid = _resolve_scenario_id(scenario_id)
    manager = get_scenario_manager()
    scenario = manager.get_engine(sid)
    config_git = get_config_git_service()

    await _reset_scenario_data(sid, db, config_git, scenario)

    return {
        "data": {
            "status": "reset",
            "scenario_id": sid,
            "current_time": 0,
            "message": f"Scenario {sid} reset to T1 (healthy baseline)",
        }
    }


@router.get("/status")
async def get_status(scenario_id: str | None = Query(None)) -> dict[str, Any]:
    from app.main import get_scenario_manager

    sid = _resolve_scenario_id(scenario_id)
    manager = get_scenario_manager()
    scenario = manager.get_engine(sid)
    info = scenario.get_scenario_info()
    catalog = manager.get_catalog_entry(sid)
    current_time = scenario.get_current_time()
    step_index = scenario.get_current_step_index()
    total_steps = scenario.get_total_steps()
    time_steps = scenario.get_time_steps()
    has_current_step_data = scenario.has_current_step_data()
    can_run_current_step = scenario.can_run_current_step()
    is_complete = scenario.is_complete()

    step_labels = scenario.get_step_labels()
    step_names = {time_steps[i]: f"T{i + 1}" for i in range(len(time_steps))}
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
                status_label = "critical"
            elif pkt_loss >= 5 or (state.latency_ms and state.latency_ms >= 50):
                status_label = "degraded"
            else:
                status_label = "healthy"
            devices.append({
                "device_id": did,
                "hostname": state.hostname,
                "vendor": state.vendor,
                "current_state": status_label,
            })
        except Exception:
            pass

    return {
        "data": {
            "scenario_id": sid,
            "scenario_name": info["name"],
            "scenario_label": catalog.get("label"),
            "vendor": catalog.get("vendor"),
            "topology_type": catalog.get("topology_type"),
            "demo_path": catalog.get("demo_path") or info.get("demo_path"),
            "affected_subnet": info.get("affected_subnet"),
            "step_labels": step_labels,
            "current_time": current_time,
            "current_step": current_step,
            "current_step_description": step_labels.get(current_step, ""),
            "total_steps": total_steps,
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
