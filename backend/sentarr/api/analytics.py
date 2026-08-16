from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from sentarr.analytics.snapshot import detect_anomalies, take_snapshot
from sentarr.db import get_session
from sentarr.models.analytics import AnalyticsSnapshot

router = APIRouter()


@router.get("")
async def list_snapshots(
    session: Session = Depends(get_session),
    metric: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    stmt = select(AnalyticsSnapshot).order_by(AnalyticsSnapshot.created_at.desc())  # type: ignore[attr-defined]
    if metric:
        stmt = stmt.where(AnalyticsSnapshot.metric == metric)
    snapshots = session.exec(stmt.limit(limit)).all()
    return [
        {
            "id": s.id,
            "bucket": s.bucket,
            "metric": s.metric,
            "value": s.value,
            "created_at": s.created_at,
        }
        for s in snapshots
    ]


@router.post("/snapshot")
async def snapshot_now(session: Session = Depends(get_session)) -> dict[str, Any]:
    take_snapshot(session)
    return {"status": "ok"}


@router.get("/anomalies")
async def get_anomalies(
    session: Session = Depends(get_session),
    metric: str = Query(...),
    window_days: int = Query(7, ge=1, le=30),
) -> list[dict[str, Any]]:
    return detect_anomalies(session, metric, window_days)
