from typing import Any

from fastapi import APIRouter

from sentarr.collectors.prowlarr import ProwlarrClient

router = APIRouter()


@router.get("")
async def list_indexers() -> dict[str, Any]:
    client = ProwlarrClient()
    try:
        indexers = client.get_indexers()
        status = client.get_indexer_status()
    finally:
        client.close()

    status_map = {s.get("indexerId"): s for s in status}
    return {
        "items": [
            {
                "id": idx.get("id"),
                "name": idx.get("name"),
                "enabled": idx.get("enable", False),
                "protocol": idx.get("protocol"),
                "status": status_map.get(idx.get("id")),
            }
            for idx in indexers
        ],
        "total": len(indexers),
    }
