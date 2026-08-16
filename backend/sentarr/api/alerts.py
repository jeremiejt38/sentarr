from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session, select

from sentarr.config import settings
from sentarr.db import get_session
from sentarr.models.arr import Alert


class ThresholdsUpdate(BaseModel):
    searched: int | None = None
    downloading: int | None = None
    importing: int | None = None
    plex_overall: int | None = None

router = APIRouter()


@router.get("")
async def list_alerts(
    session: Session = Depends(get_session),
    resolved: bool = Query(False),
    severity: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    query = select(Alert).where(Alert.resolved == resolved)  # noqa: E712
    if severity:
        query = query.where(Alert.severity == severity)
    rows = session.exec(query).all()
    total = len(rows)
    sliced = rows[offset : offset + limit]
    return {
        "items": [
            {
                "id": alert.id,
                "target_type": alert.target_type,
                "target_id": alert.target_id,
                "severity": alert.severity,
                "rule": alert.rule,
                "message": alert.message,
                "resolved": alert.resolved,
                "created_at": alert.created_at,
                "resolved_at": alert.resolved_at,
            }
            for alert in sliced
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.post("/{alert_id}/resolve")
async def resolve_alert(alert_id: int, session: Session = Depends(get_session)) -> dict[str, Any]:
    alert = session.get(Alert, alert_id)
    if not alert:
        return {"error": "Alert not found"}
    alert.resolved = True
    alert.resolved_at = datetime.now(UTC)
    session.add(alert)
    session.commit()
    return {"id": alert.id, "resolved": True}


@router.get("/thresholds")
async def get_thresholds() -> dict[str, int]:
    return {
        "searched": settings.alert_threshold_searched,
        "downloading": settings.alert_threshold_downloading,
        "importing": settings.alert_threshold_importing,
        "plex_overall": settings.alert_threshold_plex_overall,
    }


@router.post("/thresholds")
async def update_thresholds(body: ThresholdsUpdate) -> dict[str, Any]:
    if body.searched is not None:
        settings.alert_threshold_searched = body.searched
    if body.downloading is not None:
        settings.alert_threshold_downloading = body.downloading
    if body.importing is not None:
        settings.alert_threshold_importing = body.importing
    if body.plex_overall is not None:
        settings.alert_threshold_plex_overall = body.plex_overall
    return {
        "searched": settings.alert_threshold_searched,
        "downloading": settings.alert_threshold_downloading,
        "importing": settings.alert_threshold_importing,
        "plex_overall": settings.alert_threshold_plex_overall,
    }
