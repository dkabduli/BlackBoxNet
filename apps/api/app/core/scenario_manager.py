import glob
import json
import os
from typing import Any

from app.core.scenario_engine import ScenarioEngine


def vendor_group(vendor: str) -> str:
    if vendor in ("cisco-ios", "ios-xr"):
        return "cisco"
    if vendor == "junos":
        return "juniper"
    if vendor == "nokia-sros":
        return "nokia"
    return "other"


def vendor_cli_label(vendor: str) -> str:
    labels = {
        "cisco-ios": "Cisco IOS",
        "ios-xr": "Cisco IOS-XR",
        "junos": "Juniper Junos",
        "nokia-sros": "Nokia SR OS",
    }
    return labels.get(vendor, vendor)


class ScenarioManager:
    """Loads all scenario JSON fixtures and exposes per-scenario engines."""

    def __init__(self, scenarios_dir: str):
        self._scenarios_dir = scenarios_dir
        self._engines: dict[str, ScenarioEngine] = {}
        self._catalog: dict[str, dict[str, Any]] = {}

    def load_all(self) -> None:
        pattern = os.path.join(self._scenarios_dir, "*.json")
        paths = sorted(glob.glob(pattern))
        if not paths:
            raise RuntimeError(f"No scenario JSON files found in {self._scenarios_dir}")

        self._engines.clear()
        self._catalog.clear()

        presets_path = os.path.join(self._scenarios_dir, "topology-presets.json")
        topology_presets: dict[str, Any] = {}
        if os.path.isfile(presets_path):
            with open(presets_path, "r", encoding="utf-8") as f:
                topology_presets = json.load(f)

        for path in paths:
            if path.endswith("topology-presets.json"):
                continue
            with open(path, "r", encoding="utf-8") as f:
                raw = json.load(f)
            scenario_id = raw.get("id") or raw.get("scenario_id")
            if not scenario_id:
                raise ValueError(f"Scenario file missing id: {path}")

            engine = ScenarioEngine()
            engine.load_scenario(path)
            self._engines[scenario_id] = engine
            entry = self._build_catalog_entry(raw, engine)
            if scenario_id in topology_presets:
                entry["topology"] = topology_presets[scenario_id]
            elif raw.get("topology"):
                entry["topology"] = raw["topology"]
            self._catalog[scenario_id] = entry

        if not self._engines:
            raise RuntimeError("Scenario catalog is empty after load")

    def get_engine(self, scenario_id: str) -> ScenarioEngine:
        if scenario_id not in self._engines:
            raise KeyError(f"Unknown scenario_id: {scenario_id}")
        return self._engines[scenario_id]

    def has_scenario(self, scenario_id: str) -> bool:
        return scenario_id in self._engines

    def list_scenarios(self) -> list[dict[str, Any]]:
        return sorted(self._catalog.values(), key=lambda s: s.get("tab_order", 99))

    def get_catalog_entry(self, scenario_id: str) -> dict[str, Any]:
        return self._catalog[scenario_id]

    def _build_catalog_entry(self, raw: dict[str, Any], engine: ScenarioEngine) -> dict[str, Any]:
        info = engine.get_scenario_info()
        vendor = raw.get("vendor", "cisco-ios")
        return {
            "id": info["scenario_id"],
            "label": raw.get("label") or info["name"],
            "name": info["name"],
            "description": info["description"],
            "vendor": vendor,
            "vendor_group": vendor_group(vendor),
            "vendor_cli": vendor_cli_label(vendor),
            "tab_order": raw.get("tab_order", 99),
            "topology_type": raw.get("topology_type", "linear"),
            "device_count": len(engine.get_device_ids()),
            "affected_subnet": info.get("affected_subnet"),
            "demo_path": raw.get("demo_path"),
            "step_labels": raw.get("step_labels") or engine.get_step_labels(),
        }
