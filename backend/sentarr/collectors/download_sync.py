import json
import logging
import os
import re
from typing import Any

from sqlmodel import Session, select

from sentarr.collectors.download_client import DownloadClient, TorrentInfo
from sentarr.collectors.qbittorrent import QBittorrentClient
from sentarr.collectors.transmission import TransmissionClient
from sentarr.config import settings
from sentarr.models.arr import AcquisitionItem

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


def _normalize(text: str | None) -> list[str]:
    if not text:
        return []
    return [word for word in re.split(r"[^a-z0-9]+", text.lower()) if word]


def _torrents_by_hash(torrents: list[TorrentInfo]) -> dict[str, TorrentInfo]:
    by_hash: dict[str, TorrentInfo] = {}
    for torrent in torrents:
        by_hash[torrent.hash.upper()] = torrent
    return by_hash


def _match_item_to_torrent(
    item: AcquisitionItem, torrents: list[TorrentInfo], by_hash: dict[str, TorrentInfo]
) -> TorrentInfo | None:
    if item.download_id:
        by_id = by_hash.get(item.download_id.upper())
        if by_id:
            return by_id

    title_tokens = _normalize(item.title)
    if not title_tokens:
        return None
    for torrent in torrents:
        t_tokens = _normalize(torrent.name)
        if all(token in t_tokens for token in title_tokens):
            return torrent
    return None


def _build_match(item: AcquisitionItem, torrent: TorrentInfo) -> dict[str, Any]:
    return {
        "acquisition_item_id": item.id,
        "title": item.title,
        "torrent_name": torrent.name,
        "hash": torrent.hash,
        "progress_percent": round(torrent.progress * 100, 2),
        "status": torrent.status,
        "download_speed": torrent.download_speed,
        "eta_seconds": torrent.eta_seconds,
        "save_path": torrent.save_path,
        "client": torrent.name,
    }


def update_download_progress(session: Session) -> list[dict[str, Any]]:
    """Update download_progress on active acquisition items from current torrents."""
    items = session.exec(
        select(AcquisitionItem).where(AcquisitionItem.status == "downloading")
    ).all()
    torrents = list_all_torrents()
    by_hash = _torrents_by_hash(torrents)
    matches: list[dict[str, Any]] = []

    for item in items:
        torrent = _match_item_to_torrent(item, torrents, by_hash)
        if torrent:
            progress = round(torrent.progress * 100, 2)
            item.download_progress = int(progress)
            matches.append(_build_match(item, torrent))
        else:
            item.download_progress = None
        session.add(item)

    session.commit()
    return matches


def match_acquisition_to_torrents(session: Session) -> list[dict[str, Any]]:
    """Return active acquisition items matched with their download-client torrent."""
    items = session.exec(
        select(AcquisitionItem).where(AcquisitionItem.status == "downloading")
    ).all()
    torrents = list_all_torrents()
    by_hash = _torrents_by_hash(torrents)
    matches: list[dict[str, Any]] = []

    for item in items:
        torrent = _match_item_to_torrent(item, torrents, by_hash)
        if torrent:
            matches.append(_build_match(item, torrent))

    return matches
