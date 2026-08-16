"""API endpoints for plugin management."""

from typing import Any

from fastapi import APIRouter

from sentarr.plugins.manager import plugin_manager

router = APIRouter()


@router.get("")
async def list_plugins() -> dict[str, Any]:
    return {
        "items": plugin_manager.list_plugins(),
        "total": plugin_manager.plugin_count,
        "active": plugin_manager.active_count,
    }
