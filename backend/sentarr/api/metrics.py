from fastapi import APIRouter, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from sentarr.metrics.registry import build_registry

router = APIRouter()


@router.get("")
async def metrics() -> Response:
    registry = build_registry()
    data = generate_latest(registry)
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
