from collections.abc import Iterator
from typing import Any

import httpx

from sentarr.collectors.download_client import BaseDownloadClient, DownloadClientError, TorrentInfo


class QBittorrentClient(BaseDownloadClient):
    """Read-only qBittorrent Web API client."""

    def __init__(self, name: str, base_url: str, username: str = "", password: str = "") -> None:
        super().__init__(name, base_url, username, password)
        self._cookie: str | None = None
        self._login()

    def _login(self) -> None:
        if not self._username and not self._password:
            return
        try:
            response = self._client.post(
                "/api/v2/auth/login",
                data={"username": self._username, "password": self._password},
            )
            response.raise_for_status()
            self._cookie = response.headers.get("set-cookie")
        except httpx.HTTPStatusError as exc:
            raise DownloadClientError(
                f"qBittorrent login failed: HTTP {exc.response.status_code}"
            ) from exc

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        headers = kwargs.pop("headers", {})
        if self._cookie:
            headers["Cookie"] = self._cookie
        kwargs["headers"] = headers
        return super()._request(method, path, **kwargs)

    def list_torrents(self) -> Iterator[TorrentInfo]:
        data = self._request("GET", "/api/v2/torrents/info")
        if not isinstance(data, list):
            return
        for torrent in data:
            yield _normalize_torrent(torrent)


def _normalize_torrent(raw: dict[str, Any]) -> TorrentInfo:
    state = raw.get("state", "unknown")
    status = _map_status(state)
    return TorrentInfo(
        name=raw.get("name", "Unknown"),
        hash=raw.get("hash", ""),
        progress=raw.get("progress", 0.0),
        status=status,
        download_speed=raw.get("dlspeed", 0),
        eta_seconds=raw.get("eta") if raw.get("eta") and raw["eta"] >= 8640000 else None,
        save_path=raw.get("save_path"),
        labels=raw.get("tags", "").split(", ") if raw.get("tags") else None,
        raw=raw,
    )


def _map_status(state: str) -> str:
    mapping = {
        "downloading": "downloading",
        "stalledDL": "stalled",
        "metaDL": "downloading",
        "forcedDL": "downloading",
        "allocating": "downloading",
        "queuedDL": "queued",
        "uploading": "seeding",
        "stalledUP": "seeding",
        "forcedUP": "seeding",
        "queuedUP": "queued",
        "checkingUP": "checking",
        "checkingDL": "checking",
        "checkingResumeData": "checking",
        "moving": "moving",
        "pausedDL": "paused",
        "pausedUP": "paused",
        "error": "error",
        "missingFiles": "error",
        "unknown": "unknown",
    }
    return mapping.get(state, "unknown")
