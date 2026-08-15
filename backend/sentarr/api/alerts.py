from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from sentarr.db import get_session
from sentarr.models.arr import Alert

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
