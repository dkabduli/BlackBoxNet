import os
from pathlib import Path

from app.core.scenario_manager import ScenarioManager


def test_scenario_manager_loads_all_twelve_scenarios() -> None:
    scenarios_dir = str(Path(__file__).resolve().parents[3] / "packages/mock-scenarios")
    manager = ScenarioManager(scenarios_dir)
    manager.load_all()
    scenarios = manager.list_scenarios()
    ids = {s["id"] for s in scenarios}
    assert len(scenarios) == 12
    assert "acl-regression" in ids
    assert "ospf-multiarea" in ids
    assert "nokia-ldp-collision" in ids
    assert "bgp-route-leak" in ids
    assert "stp-root-hijack" in ids
    assert "juniper-bgp-hold" in ids
    assert "juniper-isis-metric" in ids
    assert "juniper-rsvp-te" in ids
    assert "juniper-firewall-policer" in ids
    assert "nokia-sdp-blackhole" in ids
    assert "nokia-vprn-leak" in ids
    assert "nokia-qos-policer" in ids
    assert any(s["vendor_group"] == "juniper" for s in scenarios)
    assert any(s["vendor_group"] == "nokia" for s in scenarios)

