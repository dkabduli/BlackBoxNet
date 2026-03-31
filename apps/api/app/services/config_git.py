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

    def write_config(
        self, device_id: str, config_text: str, timestamp: datetime
    ) -> str:
        device_dir = os.path.join(self._repo_path, device_id)
        os.makedirs(device_dir, exist_ok=True)

        ts_str = timestamp.strftime("%Y-%m-%dT%H-%M-%S")
        filename = f"{ts_str}.cfg"
        file_path = os.path.join(device_dir, filename)

        with open(file_path, "w") as f:
            f.write(config_text)

        latest_path = os.path.join(device_dir, "latest.cfg")
        with open(latest_path, "w") as f:
            f.write(config_text)

        return os.path.relpath(file_path, self._repo_path)

    def commit_changes(
        self, timestamp: datetime, changed_devices: list[str]
    ) -> str:
        self._repo.index.add("*")

        ts_str = timestamp.strftime("%Y-%m-%dT%H:%M:%SZ")
        devices_str = ", ".join(changed_devices)
        message = f"config snapshot: {ts_str} | changed: {devices_str}"

        commit = self._repo.index.commit(message)
        return commit.hexsha

    def get_config_at_commit(self, device_id: str, commit_hash: str) -> str | None:
        try:
            commit = self._repo.commit(commit_hash)
            for blob in commit.tree.traverse():
                if device_id in blob.path and blob.path.endswith(".cfg"):
                    if "latest.cfg" not in blob.path:
                        return blob.data_stream.read().decode("utf-8")
        except Exception:
            pass
        return None

    def get_latest_commit_hash(self) -> str:
        return self._repo.head.commit.hexsha

    def cleanup(self) -> None:
        """Remove all config files and reset for simulation reset."""
        import shutil
        for item in os.listdir(self._repo_path):
            item_path = os.path.join(self._repo_path, item)
            if item == ".git" or item == ".gitignore":
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
