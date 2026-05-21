import os
from datetime import datetime, timezone
import git


class ConfigGitService:
    def __init__(self, repo_path: str):
        self._repo_path = repo_path
        self._repo: git.Repo | None = None
        self._init_repo()

    def _init_repo(self) -> None:
        os.makedirs(self._repo_path, exist_ok=True)
        try:
            self._repo = git.Repo(self._repo_path)
        except git.InvalidGitRepositoryError:
            self._repo = git.Repo.init(self._repo_path)
            gitignore = os.path.join(self._repo_path, ".gitignore")
            with open(gitignore, "w") as f:
                f.write("*.pyc\n__pycache__/\n")
            self._repo.index.add([".gitignore"])
            self._repo.index.commit("Initial repository setup")

    def _device_dir(self, scenario_id: str, device_id: str) -> str:
        return os.path.join(self._repo_path, "configs", scenario_id, device_id)

    def write_config(
        self,
        scenario_id: str,
        device_id: str,
        config_text: str,
        timestamp: datetime,
        step_label: str | None = None,
    ) -> str:
        device_dir = self._device_dir(scenario_id, device_id)
        os.makedirs(device_dir, exist_ok=True)

        ts_str = timestamp.strftime("%Y-%m-%dT%H-%M-%S")
        filename = f"{step_label or ts_str}.txt"
        file_path = os.path.join(device_dir, filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(config_text)

        latest_path = os.path.join(device_dir, "latest.txt")
        with open(latest_path, "w", encoding="utf-8") as f:
            f.write(config_text)

        return os.path.relpath(file_path, self._repo_path)

    def commit_changes(
        self,
        scenario_id: str,
        timestamp: datetime,
        changed_devices: list[str],
    ) -> str:
        self._repo.index.add("*")

        ts_str = timestamp.strftime("%Y-%m-%dT%H-%M-%SZ")
        devices_str = ", ".join(changed_devices)
        message = f"[{scenario_id}] config snapshot: {ts_str} | changed: {devices_str}"

        commit = self._repo.index.commit(message)
        return commit.hexsha

    def get_config_at_commit(
        self, scenario_id: str, device_id: str, commit_hash: str
    ) -> str | None:
        prefix = f"configs/{scenario_id}/{device_id}"
        try:
            commit = self._repo.commit(commit_hash)
            newest = None
            for blob in commit.tree.traverse():
                if blob.path.startswith(prefix) and blob.path.endswith(".txt"):
                    if "latest.txt" in blob.path:
                        continue
                    newest = blob
            if newest:
                return newest.data_stream.read().decode("utf-8")
        except Exception:
            pass
        return None

    def get_latest_commit_hash(self) -> str:
        return self._repo.head.commit.hexsha

    def cleanup(self) -> None:
        """Remove all config namespaces and reset for full wipe."""
        import shutil

        for item in os.listdir(self._repo_path):
            item_path = os.path.join(self._repo_path, item)
            if item in (".git", ".gitignore"):
                continue
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)

        self._repo.index.add("*")
        try:
            self._repo.index.commit("Reset: cleared all configs")
        except Exception:
            pass

    def seed_from_package_configs(self, package_configs_dir: str) -> bool:
        """Copy bundled configs into the repo when configs/ is empty (Render cold deploy)."""
        import shutil

        dest = os.path.join(self._repo_path, "configs")
        if os.path.isdir(dest):
            try:
                if any(os.scandir(dest)):
                    return False
            except OSError:
                pass
        if not os.path.isdir(package_configs_dir):
            return False

        os.makedirs(self._repo_path, exist_ok=True)
        shutil.copytree(package_configs_dir, dest, dirs_exist_ok=True)
        self._repo.index.add("*")
        try:
            self._repo.index.commit("Seed configs from mock-scenarios package")
        except Exception:
            pass
        return True

    def cleanup_scenario(self, scenario_id: str) -> None:
        """Remove one scenario namespace under configs/."""
        import shutil

        scenario_path = os.path.join(self._repo_path, "configs", scenario_id)
        if os.path.isdir(scenario_path):
            shutil.rmtree(scenario_path)

        self._repo.index.add("*")
        try:
            self._repo.index.commit(f"Reset: cleared scenario {scenario_id}")
        except Exception:
            pass
