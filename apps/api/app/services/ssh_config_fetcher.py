from dataclasses import dataclass

import paramiko


@dataclass
class RealDeviceSSHConfig:
    host: str
    port: int
    username: str
    password: str | None = None
    private_key_path: str | None = None
    private_key_passphrase: str | None = None
    command: str = "show running-config"
    timeout_seconds: int = 15
    scenario_device_id: str | None = None


class SSHConfigFetcher:
    def __init__(self, config: RealDeviceSSHConfig):
        self._config = config

    def fetch_running_config(self) -> str:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connect_kwargs: dict[str, object] = {
            "hostname": self._config.host,
            "port": self._config.port,
            "username": self._config.username,
            "timeout": self._config.timeout_seconds,
            "banner_timeout": self._config.timeout_seconds,
            "auth_timeout": self._config.timeout_seconds,
            "look_for_keys": self._config.private_key_path is None,
        }

        if self._config.private_key_path:
            connect_kwargs["key_filename"] = self._config.private_key_path
            if self._config.private_key_passphrase:
                connect_kwargs["passphrase"] = self._config.private_key_passphrase
        if self._config.password:
            connect_kwargs["password"] = self._config.password

        try:
            client.connect(**connect_kwargs)
            _stdin, stdout, stderr = client.exec_command(
                self._config.command,
                timeout=self._config.timeout_seconds,
            )
            output = stdout.read().decode("utf-8", errors="replace")
            err_output = stderr.read().decode("utf-8", errors="replace").strip()
            exit_status = stdout.channel.recv_exit_status()
        except Exception as exc:
            raise RuntimeError(
                f"SSH config pull failed for {self._config.host}:{self._config.port}: {exc}"
            ) from exc
        finally:
            client.close()

        if exit_status != 0:
            raise RuntimeError(
                f"SSH config pull failed for {self._config.host}:{self._config.port}: {err_output or 'non-zero exit status'}"
            )
        if not output.strip():
            raise RuntimeError(
                f"SSH config pull failed for {self._config.host}:{self._config.port}: empty config output"
            )
        return output
