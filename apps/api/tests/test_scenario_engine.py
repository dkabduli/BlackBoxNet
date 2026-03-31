import os
from pathlib import Path

from app.core.scenario_engine import ScenarioEngine


def load_engine() -> ScenarioEngine:
    engine = ScenarioEngine()
    scenario_path = os.getenv("SCENARIO_PATH")
    if scenario_path is None:
        scenario_path = str(Path(__file__).resolve().parents[2] / "packages/mock-scenarios/acl-regression.json")
    engine.load_scenario(str(scenario_path))
    return engine


def test_scenario_tracks_pending_and_collected_steps() -> None:
    engine = load_engine()

    assert engine.get_current_time() == 0
    assert engine.can_run_current_step() is True
    assert engine.has_current_step_data() is False
    assert engine.is_complete() is False

    engine.mark_current_step_collected()

    assert engine.can_run_current_step() is False
    assert engine.has_current_step_data() is True

    engine.advance_time()

    assert engine.get_current_time() == 60
    assert engine.can_run_current_step() is True
    assert engine.has_current_step_data() is False


def test_scenario_only_completes_after_final_step_is_collected() -> None:
    engine = load_engine()

    for _ in range(engine.get_total_steps() - 1):
        engine.mark_current_step_collected()
        engine.advance_time()

    assert engine.get_current_time() == 240
    assert engine.is_complete() is False
    assert engine.can_run_current_step() is True

    engine.mark_current_step_collected()

    assert engine.is_complete() is True
    assert engine.can_run_current_step() is False
