import os
from pathlib import Path

from app.services.config_git import ConfigGitService


def test_cleanup_scenario_leaves_other_scenarios(tmp_path: Path) -> None:
    git_svc = ConfigGitService(str(tmp_path))
    configs = tmp_path / "configs"
    scenario_a = configs / "scenario-a" / "device-1"
    scenario_b = configs / "scenario-b" / "device-2"
    scenario_a.mkdir(parents=True)
    scenario_b.mkdir(parents=True)
    (scenario_a / "T1.txt").write_text("config a", encoding="utf-8")
    (scenario_b / "T1.txt").write_text("config b", encoding="utf-8")
    git_svc._repo.index.add("*")
    git_svc._repo.index.commit("test setup")

    git_svc.cleanup_scenario("scenario-a")

    assert not (configs / "scenario-a").exists()
    assert (configs / "scenario-b" / "T1.txt").read_text(encoding="utf-8") == "config b"


def test_seed_from_package_configs_only_when_empty(tmp_path: Path) -> None:
    package_configs = Path(__file__).resolve().parents[3] / "packages/mock-scenarios/configs"
    if not package_configs.is_dir():
        return

    git_svc = ConfigGitService(str(tmp_path))
    seeded = git_svc.seed_from_package_configs(str(package_configs))
    assert seeded is True
    assert (tmp_path / "configs" / "acl-regression").is_dir()

    git_svc2 = ConfigGitService(str(tmp_path))
    seeded_again = git_svc2.seed_from_package_configs(str(package_configs))
    assert seeded_again is False
