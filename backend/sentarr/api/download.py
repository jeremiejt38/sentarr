from typing import Any

from fastapi import APIRouter

from sentarr.collectors.download_sync import list_all_torrents

router = APIRouter()


@router.get("")
async def list_downloads() -> list[dict[str, Any]]:
    torrents = list_all_torrents()
    return [
        {
            "name": torrent.name,
            "hash": torrent.hash,
            "progress": round(torrent.progress * 100, 2),
            "status": torrent.status,
            "download_speed": torrent.download_speed,
            "eta_seconds": torrent.eta_seconds,
            "save_path": torrent.save_path,
            "labels": torrent.labels,
        }
        for torrent in torrents
    ]
