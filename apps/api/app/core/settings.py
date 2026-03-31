from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore", env_file=".env", case_sensitive=False)

    real_device_enabled: bool = Field(default=False, alias="REAL_DEVICE_ENABLED")
    real_device_host: str | None = Field(default=None, alias="REAL_DEVICE_HOST")
    real_device_port: int = Field(default=22, alias="REAL_DEVICE_PORT")
    real_device_username: str | None = Field(default=None, alias="REAL_DEVICE_USERNAME")
    real_device_password: str | None = Field(default=None, alias="REAL_DEVICE_PASSWORD")
    real_device_private_key_path: str | None = Field(default=None, alias="REAL_DEVICE_PRIVATE_KEY_PATH")
    real_device_private_key_passphrase: str | None = Field(default=None, alias="REAL_DEVICE_PRIVATE_KEY_PASSPHRASE")
    real_device_scenario_device_id: str | None = Field(default=None, alias="REAL_DEVICE_SCENARIO_DEVICE_ID")
    real_device_command: str = Field(default="show running-config", alias="REAL_DEVICE_COMMAND")
    real_device_timeout_seconds: int = Field(default=15, alias="REAL_DEVICE_TIMEOUT_SECONDS")


@lru_cache
def get_settings() -> Settings:
    return Settings()
