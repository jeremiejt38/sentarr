from collections.abc import Iterator
from typing import Any

import httpx

from sentarr.collectors.download_client import BaseDownloadClient, DownloadClientError, TorrentInfo


class TransmissionClient(BaseDownloadClient):
    """Read-only Transmission RPC client."""

    def __init__(self, name: str, base_url: str, username: str = "", password: str = "") -> None:
        super().__init__(name, base_url, username, password)
        self._session_id: str | None = None
        self._tag = 1

    def _rpc(self, method: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        body: dict[str, Any] = {"method": method, "arguments": arguments or {}}
        headers: dict[str, str] = {}
        if self._session_id:
            headers["X-Transmission-Session-Id"] = self._session_id
        auth = (self._username, self._password) if self._username else None
        try:
            response = self._client.post(
                "/transmission/rpc",
                json=body,
                headers=headers,
                auth=auth,  # type: ignore[arg-type]
            )
            if response.status_code == 409:
                self._session_id = response.headers.get("X-Transmission-Session-Id")
                if not self._session_id:
                    raise DownloadClientError("Transmission session id not provided")
                return self._rpc(method, arguments)
            response.raise_for_status()
            result = response.json()
            if result.get("result") != "success":
                raise DownloadClientError(f"Transmission RPC error: {result.get('result')}")
            return dict(result.get("arguments", {}))
        except httpx.HTTPStatusError as exc:
            raise DownloadClientError(f"HTTP {exc.response.status_code} from {self._name}") from exc

    def list_torrents(self) -> Iterator[TorrentInfo]:
        arguments = {
            "fields": [
                "id",
                "hashString",
                "name",
                "status",
                "percentDone",
                "rateDownload",
                "eta",
                "downloadDir",
                "labels",
                "error",
                "errorString",
            ]
        }
        result = self._rpc("torrent-get", arguments)
        torrents = result.get("torrents", [])
        for torrent in torrents:
            yield _normalize_torrent(torrent)


def _normalize_torrent(raw: dict[str, Any]) -> TorrentInfo:
    status_code = raw.get("status", 0)
    return TorrentInfo(
        name=raw.get("name", "Unknown"),
        hash=raw.get("hashString", ""),
        progress=raw.get("percentDone", 0.0),
        status=_map_status(status_code, raw.get("error", 0)),
        download_speed=raw.get("rateDownload", 0),
        eta_seconds=raw.get("eta") if raw.get("eta") and raw["eta"] >= 0 else None,
        save_path=raw.get("downloadDir"),
        labels=raw.get("labels") if isinstance(raw.get("labels"), list) else None,
        raw=raw,
    )


def _map_status(status: int, error: int) -> str:
    if error:
        return "error"
    mapping = {
        0: "paused",
        1: "queued",
        2: "queued",
        3: "queued",
        4: "downloading",
        5: "checking",
        6: "seeding",
    }
    return mapping.get(status, "unknown")
