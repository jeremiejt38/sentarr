import logging
from typing import Any

from fastapi import APIRouter, Query

from sentarr.collectors.prowlarr import ProwlarrClient, get_prowlarr_instances

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
async def list_indexers(source: str | None = Query(None)) -> dict[str, Any]:
    """List indexers from all Prowlarr instances (or a specific one)."""
    instances = get_prowlarr_instances()
    if not instances:
        return {"items": [], "total": 0}

    all_items: list[dict[str, Any]] = []
    for inst in instances:
        inst_name = inst.get("name", "default")
        if source and inst_name != source:
            continue
        url = inst.get("url", "")
        if not url:
            continue
        client = ProwlarrClient(base_url=url, api_key=inst.get("api_key", ""))
        try:
            indexers = client.get_indexers()
            status = client.get_indexer_status()
        except Exception:
            logger.exception("Failed to fetch indexers from %s", inst_name)
            continue
        finally:
            client.close()

        status_map = {s.get("indexerId"): s for s in status}
        for idx in indexers:
            all_items.append(
                {
                    "id": idx.get("id"),
                    "name": idx.get("name"),
                    "enabled": idx.get("enable", False),
                    "protocol": idx.get("protocol"),
                    "status": status_map.get(idx.get("id")),
                    "source": inst_name,
                }
            )

    return {"items": all_items, "total": len(all_items)}


@router.get("/stats")
async def indexer_stats(source: str | None = Query(None)) -> dict[str, Any]:
    """Get indexer statistics from all Prowlarr instances."""
    instances = get_prowlarr_instances()
    if not instances:
        return {"sources": []}

    sources: list[dict[str, Any]] = []
    for inst in instances:
        inst_name = inst.get("name", "default")
        if source and inst_name != source:
            continue
        url = inst.get("url", "")
        if not url:
            continue
        client = ProwlarrClient(base_url=url, api_key=inst.get("api_key", ""))
        try:
            stats = client.get_indexer_stats()
            sources.append({"source": inst_name, "stats": stats})
        except Exception:
            logger.exception("Failed to fetch stats from %s", inst_name)
        finally:
            client.close()

    return {"sources": sources}
