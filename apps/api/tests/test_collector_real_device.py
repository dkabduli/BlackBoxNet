from dataclasses import dataclass

from app.core.scenario_engine import DeviceState
from app.services.collector import CollectorService


@dataclass
class FakeFetcherConfig:
    scenario_device_id: str
    host: str = "192.0.2.10"


class FakeFetcher:
    def __init__(self, scenario_device_id: str, config_text: str) -> None:
        self._config = FakeFetcherConfig(scenario_device_id=scenario_device_id)
        self._config_text = config_text

    def fetch_running_config(self) -> str:
        return self._config_text


class FakeScenario:
    def get_config_content(self, _path: str) -> str:
        return "hostname simulated-device\n"


def make_device_state(device_id: str) -> DeviceState:
    return DeviceState(
        device_id=device_id,
        hostname="edge-router-1",
        vendor="cisco-ios",
        role="edge-router",
        management_ip="192.168.1.1",
        timestamp=60,
        config_path="configs/edge-router-1-baseline.cfg",
        cpu_usage=10.0,
        memory_usage=20.0,
        latency_ms=5.0,
        packet_loss_pct=0.0,
        interfaces=[],
        tags=[],
    )


def test_collector_uses_real_device_override_and_redacts_config() -> None:
    fetcher = FakeFetcher(
        scenario_device_id="edge-router-1",
        config_text="username admin secret supersecret\nhostname edge-router-1\n",
    )
    collector = CollectorService(FakeScenario(), None, None, fetcher)  # type: ignore[arg-type]

    config_text, config_source, metadata = collector._get_config_for_device(make_device_state("edge-router-1"))

    assert config_source == "ssh"
    assert metadata["redacted"] is True
    assert metadata["real_device_host"] == "192.0.2.10"
    assert "supersecret" not in config_text
    assert "<redacted>" in config_text


def test_collector_keeps_simulated_config_for_other_devices() -> None:
    fetcher = FakeFetcher(
        scenario_device_id="edge-router-1",
        config_text="hostname real-device\n",
    )
    collector = CollectorService(FakeScenario(), None, None, fetcher)  # type: ignore[arg-type]

    config_text, config_source, metadata = collector._get_config_for_device(make_device_state("dist-switch-1"))

    assert config_source == "simulation"
    assert metadata["config_source"] == "simulation"
    assert config_text == "hostname simulated-device\n"
