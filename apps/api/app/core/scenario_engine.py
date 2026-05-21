import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass
class InterfaceState:
    name: str
    admin_state: str
    oper_state: str
    rx_errors: int = 0
    tx_errors: int = 0
    description: str | None = None
    ip_address: str | None = None


@dataclass
class DeviceState:
    device_id: str
    hostname: str
    vendor: str
    role: str
    management_ip: str
    timestamp: int
    config_path: str
    cpu_usage: float
    memory_usage: float
    latency_ms: float | None
    packet_loss_pct: float
    interfaces: list[InterfaceState] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


class ScenarioEngine:
    def __init__(self):
        self._scenario: dict[str, Any] | None = None
        self._devices: dict[str, dict] = {}
        self._time_steps: list[int] = []
        self._current_step_index: int = 0
        self._last_collected_step_index: int = -1
        self._scenario_base_path: str = ""

    def load_scenario(self, scenario_path: str) -> None:
        with open(scenario_path, "r") as f:
            self._scenario = json.load(f)

        self._scenario_base_path = os.path.dirname(scenario_path)
        self._time_steps = self._scenario["time_steps"]
        self._current_step_index = 0
        self._last_collected_step_index = -1

        for device in self._scenario["devices"]:
            self._devices[device["device_id"]] = device

    def get_device_state(self, device_id: str, timestamp: int) -> DeviceState:
        if device_id not in self._devices:
            raise ValueError(f"Unknown device: {device_id}")

        device = self._devices[device_id]
        state = self._find_state_at_timestamp(device["states"], timestamp)
        if state is None:
            raise ValueError(f"No state found for {device_id} at t={timestamp}")

        interfaces = [
            InterfaceState(
                name=iface["name"],
                admin_state=iface["admin_state"],
                oper_state=iface["oper_state"],
                rx_errors=iface.get("rx_errors", 0),
                tx_errors=iface.get("tx_errors", 0),
                description=iface.get("description"),
                ip_address=iface.get("ip_address"),
            )
            for iface in state.get("interfaces", [])
        ]

        return DeviceState(
            device_id=device["device_id"],
            hostname=device["hostname"],
            vendor=device["vendor"],
            role=device["role"],
            management_ip=device["management_ip"],
            timestamp=state["timestamp"],
            config_path=state["config_path"],
            cpu_usage=state["cpu_usage"],
            memory_usage=state["memory_usage"],
            latency_ms=state.get("latency_ms"),
            packet_loss_pct=state["packet_loss_pct"],
            interfaces=interfaces,
            tags=state.get("tags", []),
        )

    def get_all_devices_state(self, timestamp: int) -> list[DeviceState]:
        return [
            self.get_device_state(device_id, timestamp)
            for device_id in self._devices
        ]

    def get_config_content(self, config_path: str) -> str:
        full_path = os.path.join(self._scenario_base_path, config_path)
        with open(full_path, "r") as f:
            return f.read()

    def advance_time(self) -> int:
        if self._current_step_index < len(self._time_steps) - 1:
            self._current_step_index += 1
        return self.get_current_time()

    def mark_current_step_collected(self) -> None:
        self._last_collected_step_index = max(
            self._last_collected_step_index, self._current_step_index
        )

    def get_current_time(self) -> int:
        return self._time_steps[self._current_step_index]

    def get_current_step_index(self) -> int:
        return self._current_step_index

    def get_total_steps(self) -> int:
        return len(self._time_steps)

    def get_time_steps(self) -> list[int]:
        return list(self._time_steps)

    def get_device_ids(self) -> list[str]:
        return list(self._devices.keys())

    def get_scenario_id(self) -> str:
        return self._scenario.get("id") or self._scenario["scenario_id"]

    def get_scenario_info(self) -> dict[str, Any]:
        return {
            "scenario_id": self.get_scenario_id(),
            "name": self._scenario["name"],
            "description": self._scenario["description"],
            "affected_subnet": self._scenario.get("affected_subnet"),
            "duration_seconds": self._scenario["duration_seconds"],
            "topology_type": self._scenario.get("topology_type", "linear"),
            "demo_path": self._scenario.get("demo_path"),
        }

    def get_step_labels(self) -> dict[str, str]:
        labels = self._scenario.get("step_labels")
        if labels:
            return labels
        step_names = {0: "T1", 60: "T2", 120: "T3", 180: "T4", 240: "T5"}
        return {
            step_names.get(t, f"T{i + 1}"): self._scenario.get("step_descriptions", {}).get(
                step_names.get(t, f"T{i + 1}"), f"Checkpoint at {t}s"
            )
            for i, t in enumerate(self._time_steps)
        }

    def get_correlation_config(self) -> dict[str, Any]:
        return self._scenario.get("correlation", {})

    def get_correlation_rules(self) -> list[dict[str, Any]]:
        return self._scenario.get("correlation_rules", [])

    def can_advance(self) -> bool:
        return self._current_step_index < len(self._time_steps) - 1

    def has_current_step_data(self) -> bool:
        return self._last_collected_step_index >= self._current_step_index

    def can_run_current_step(self) -> bool:
        return not self.has_current_step_data()

    def is_complete(self) -> bool:
        return (
            self._current_step_index == len(self._time_steps) - 1
            and self.has_current_step_data()
        )

    def reset(self) -> None:
        self._current_step_index = 0
        self._last_collected_step_index = -1

    def _find_state_at_timestamp(
        self, states: list[dict], timestamp: int
    ) -> dict | None:
        result = None
        for state in states:
            if state["timestamp"] <= timestamp:
                result = state
            else:
                break
        return result
