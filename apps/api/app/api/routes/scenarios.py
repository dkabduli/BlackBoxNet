from typing import Any

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/api", tags=["scenarios"])


@router.get("/scenarios")
async def list_scenarios() -> dict[str, Any]:
    from app.main import get_scenario_manager

    manager = get_scenario_manager()
    return {"data": manager.list_scenarios(), "meta": {"total": len(manager.list_scenarios())}}


@router.get("/diff/{scenario_id}/{device_id}")
async def get_scenario_device_diff(
    scenario_id: str,
    device_id: str,
) -> dict[str, Any]:
    """Unified diff between last two committed config snapshots for a device."""
    from app.main import get_scenario_manager, get_config_git_service
    import difflib

    manager = get_scenario_manager()
    if not manager.has_scenario(scenario_id):
        raise HTTPException(status_code=404, detail="Scenario not found")

    engine = manager.get_engine(scenario_id)
    config_git = get_config_git_service()
    device_dir = config_git._device_dir(scenario_id, device_id)

    import os

    if not os.path.isdir(device_dir):
        raise HTTPException(status_code=404, detail="No configs committed for device")

    files = sorted(
        f for f in os.listdir(device_dir)
        if f.endswith(".txt") and f != "latest.txt"
    )
    if len(files) < 2:
        raise HTTPException(status_code=404, detail="Need at least two snapshots for diff")

    prev_name, curr_name = files[-2], files[-1]
    with open(os.path.join(device_dir, prev_name), encoding="utf-8") as f:
        old_content = f.read()
    with open(os.path.join(device_dir, curr_name), encoding="utf-8") as f:
        new_content = f.read()

    diff_lines = list(
        difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=prev_name,
            tofile=curr_name,
        )
    )
    vendor = "nokia-sros" if scenario_id == "nokia-ldp-collision" else "cisco-ios"
    if vendor == "nokia-sros":
        from app.core.semantic_extraction.nokia_sros import NokiaSROSExtractor

        semantic = [s.to_dict() for s in NokiaSROSExtractor().extract_changes(
            "".join(diff_lines), old_content, new_content
        )]
    else:
        from app.core.semantic_extraction.cisco_ios import CiscoIOSExtractor

        semantic = [s.to_dict() for s in CiscoIOSExtractor().extract_changes(
            "".join(diff_lines), old_content, new_content
        )]

    return {
        "data": {
            "scenario_id": scenario_id,
            "device_id": device_id,
            "from_file": prev_name,
            "to_file": curr_name,
            "diff_text": "".join(diff_lines),
            "semantic_summary": semantic,
            "vendor": vendor,
        }
    }
