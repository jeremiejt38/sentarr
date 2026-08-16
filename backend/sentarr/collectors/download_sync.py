import json
import logging
import os
from typing import Any

from sentarr.collectors.download_client import DownloadClient, TorrentInfo
from sentarr.collectors.qbittorrent import QBittorrentClient
from sentarr.collectors.transmission import TransmissionClient
from sentarr.config import settings

logger = logging.getLogger(__name__)


def _resolve_password(password_env: str | None) -> str:
    if not password_env:
        return ""
    return os.environ.get(password_env, "")


def make_download_client(descriptor: dict[str, Any]) -> DownloadClient:
    client_type = descriptor.get("type", "qbittorrent")
    name = descriptor.get("name", client_type)
    url = descriptor.get("url", "")
    username = descriptor.get("username", "")
    password = _resolve_password(descriptor.get("password_env"))
    if client_type == "qbittorrent":
        return QBittorrentClient(name, url, username, password)
    if client_type == "transmission":
        return TransmissionClient(name, url, username, password)
    raise ValueError(f"Unsupported download client type: {client_type}")


def parse_download_clients(raw: str) -> list[dict[str, Any]]:
    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(items, list):
        return []
    return items


def get_download_clients() -> list[DownloadClient]:
    return [make_download_client(d) for d in parse_download_clients(settings.download_clients)]


def list_all_torrents() -> list[TorrentInfo]:
    torrents: list[TorrentInfo] = []
    for client in get_download_clients():
        try:
            with client:
                for torrent in client.list_torrents():
                    torrents.append(torrent)
        except Exception:
            logger.exception("Failed to list torrents from %s", client.name())
    return torrents
