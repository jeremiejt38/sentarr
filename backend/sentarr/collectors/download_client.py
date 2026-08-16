import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class TorrentInfo:
    name: str
    hash: str
    progress: float  # 0.0 - 1.0
    status: str  # downloading / seeding / paused / stalled / error
    download_speed: int  # bytes/s
    eta_seconds: int | None
    save_path: str | None
    labels: list[str] | None
    raw: dict[str, Any] | None = None


class DownloadClientError(Exception):
    pass


class DownloadClient(ABC):
    """Abstract read-only client for download clients such as qBittorrent or Transmission."""

    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def list_torrents(self) -> Iterator[TorrentInfo]:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    def __enter__(self) -> "DownloadClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class BaseDownloadClient(DownloadClient):
    """Common HTTP helpers for download clients."""

    def __init__(self, name: str, base_url: str, username: str = "", password: str = "") -> None:
        self._name = name
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._client = httpx.Client(
            base_url=self._base_url,
            timeout=httpx.Timeout(30.0),
        )

    def name(self) -> str:
        return self._name

    def close(self) -> None:
        self._client.close()

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        if method.upper() != "GET":
            raise DownloadClientError(f"Only GET requests are allowed (got {method})")
        try:
            response = self._client.request(method, path, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("%s %s returned %s", self._name, path, exc.response.status_code)
            raise DownloadClientError(f"HTTP {exc.response.status_code} from {self._name}") from exc
        except httpx.RequestError as exc:
            logger.error("Request to %s failed: %s", self._name, exc)
            raise DownloadClientError(f"Request failed for {self._name}") from exc
