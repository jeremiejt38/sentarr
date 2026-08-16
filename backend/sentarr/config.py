import json
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

    # Plex (single-server legacy, still used as fallback)
    plex_url: str = "http://plex:32400"
    plex_token: str = Field(default="", description="Plex X-Plex-Token")
    plex_log_path: str = (
        "/config/Library/Application Support/Plex Media Server/Logs/Plex Media Server.log"
    )

    # Plex multi-server (JSON array)
    # Format: [{"name":"main","url":"http://plex:32400","token":"...","log_path":"..."}]
    plex_servers: str = "[]"

    # *arr clients (V2)
    radarr_urls: str = "[]"
    sonarr_urls: str = "[]"
    arr_poll_interval_seconds: int = 60
    stall_threshold_minutes: int = 30
    webhook_url: str | None = None

    # Download clients (V2)
    download_clients: str = "[]"

    # Health score thresholds (V2)
    health_threshold_warning: int = 80
    health_threshold_critical: int = 50

    # Auth (V3)
    auth_mode: str = "none"  # none | api_key | forms | external
    sentarr_admin_api_key: str = ""  # bootstrap admin key from env

    # Extensions (V3) — single-instance legacy
    bazarr_url: str | None = None
    bazarr_api_key: str | None = None
    prowlarr_url: str | None = None
    prowlarr_api_key: str | None = None

    # Extensions (V3) — multi-instance JSON
    # Format: [{"name":"bazarr-main","url":"http://bazarr:6767","api_key":"..."}]
    bazarr_instances: str = "[]"
    # Format: [{"name":"prowlarr-main","url":"http://prowlarr:9696","api_key":"..."}]
    prowlarr_instances: str = "[]"

    # Notifications (V3)
    notification_channels: str = "[]"

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

    @property
    def parsed_plex_servers(self) -> list[dict[str, Any]]:
        """Return list of Plex server configs from JSON env, with single-server fallback."""
        try:
            servers = json.loads(self.plex_servers)
        except json.JSONDecodeError:
            servers = []
        if not isinstance(servers, list):
            servers = []
        if not servers and self.plex_token:
            servers = [
                {
                    "name": "default",
                    "url": self.plex_url,
                    "token": self.plex_token,
                    "log_path": self.plex_log_path,
                }
            ]
        return servers


settings = Settings()
