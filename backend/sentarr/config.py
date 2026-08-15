from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", REPO_ROOT / ".env.local"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Plex
    plex_url: str = "http://plex:32400"
    plex_token: str = Field(default="", description="Plex X-Plex-Token")
    plex_log_path: str = (
        "/config/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log"
    )

    # Application
    database_url: str = "sqlite:///app/data/sentarr.db"
    log_level: str = "INFO"
    poll_interval_seconds: int = 60
    log_tail_interval_seconds: int = 5
    history_retention_days: int = 30
    retro_scan: bool = True
    libraries_filter: str = ""
    plex_pass_enabled: str = "auto"  # auto | true | false

    # API
    host: str = "0.0.0.0"
    port: int = 8000

    @field_validator("libraries_filter", mode="before")
    @classmethod
    def _split_libraries(cls, value: str | list[Any] | None) -> str:
        if value is None:
            return ""
        if isinstance(value, list):
            return ",".join(str(item) for item in value)
        return str(value)

    @property
    def libraries_filter_list(self) -> list[str]:
        if not self.libraries_filter:
            return []
        return [name.strip() for name in self.libraries_filter.split(",") if name.strip()]

    @property
    def data_dir(self) -> Path:
        path = Path(self.database_url.replace("sqlite:///", "").replace("sqlite://", "")).parent
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
