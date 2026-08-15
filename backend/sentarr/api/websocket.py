import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
logger = logging.getLogger(__name__)

connected: set[WebSocket] = set()


@router.websocket("")
async def websocket_endpoint(websocket: WebSocket) -> None:
    await websocket.accept()
    connected.add(websocket)
    try:
        while True:
            # Attendre les messages clients éventuels
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                logger.debug("WebSocket message received: %s", message)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON received on WebSocket")
    except WebSocketDisconnect:
        connected.discard(websocket)
    except Exception:
        logger.exception("WebSocket error")
        connected.discard(websocket)


async def broadcast(message: dict[str, Any]) -> None:
    payload = json.dumps(message)
    disconnected = set()
    for ws in connected:
        try:
            await ws.send_text(payload)
        except Exception:
            disconnected.add(ws)
    for ws in disconnected:
        connected.discard(ws)
