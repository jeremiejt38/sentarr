from typing import Any

from fastapi import APIRouter

from sentarr.notifications.engine import notify

router = APIRouter()


@router.post("/test")
async def test_notification(payload: dict[str, Any]) -> dict[str, bool]:
    title = payload.get("title", "Test Sentarr")
    body = payload.get("body", "Ceci est une notification de test.")
    event_type = payload.get("event_type", "info")
    ok = notify(title, body, event_type)
    return {"sent": ok}
