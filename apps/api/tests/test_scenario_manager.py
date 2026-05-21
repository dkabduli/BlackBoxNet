import os
from pathlib import Path

from app.core.scenario_manager import ScenarioManager


def test_scenario_manager_loads_all_five_scenarios() -> None:
    scenarios_dir = str(Path(__file__).resolve().parents[3] / "packages/mock-scenarios")
    manager = ScenarioManager(scenarios_dir)
    manager.load_all()
    scenarios = manager.list_scenarios()
    ids = {s["id"] for s in scenarios}
    assert len(scenarios) == 6
    assert "acl-regression" in ids
    assert "ospf-multiarea" in ids
    assert "nokia-ldp-collision" in ids
    assert "bgp-route-leak" in ids
    assert "stp-root-hijack" in ids
    assert "juniper-bgp-hold" in ids
    assert any(s["vendor_group"] == "juniper" for s in scenarios)
