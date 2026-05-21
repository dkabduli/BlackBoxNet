import pytest
from fastapi import HTTPException

from app.api.routes.simulation import _resolve_scenario_id


def test_resolve_unknown_scenario_raises_404(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeManager:
        def has_scenario(self, scenario_id: str) -> bool:
            return scenario_id == "acl-regression"

    monkeypatch.setattr("app.main.get_scenario_manager", lambda: FakeManager())

    with pytest.raises(HTTPException) as exc:
        _resolve_scenario_id("not-a-scenario")
    assert exc.value.status_code == 404


def test_resolve_known_scenario_returns_id(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeManager:
        def has_scenario(self, scenario_id: str) -> bool:
            return scenario_id == "acl-regression"

    monkeypatch.setattr("app.main.get_scenario_manager", lambda: FakeManager())

    assert _resolve_scenario_id("acl-regression") == "acl-regression"
    assert _resolve_scenario_id(None) == "acl-regression"
