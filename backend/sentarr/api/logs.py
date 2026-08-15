from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from sentarr.db import get_session
from sentarr.models.plex import LogEventRaw

router = APIRouter()


@router.get("/unparsed")
async def list_unparsed_logs(
    session: Session = Depends(get_session),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    query = session.query(LogEventRaw).filter(LogEventRaw.parsed.is_(False))  # type: ignore
    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    return {
        "items": [
            {
                "id": row.id,
                "timestamp": row.timestamp,
                "raw_line": row.raw_line,
            }
            for row in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


@router.get("/events")
async def list_parsed_events(
    session: Session = Depends(get_session),
    target_type: str | None = Query(None),
    target_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    query = session.query(LogEventRaw).filter(LogEventRaw.parsed.is_(True))  # type: ignore
    if target_type is not None:
        query = query.filter(LogEventRaw.correlated_to_type == target_type)  # type: ignore
    if target_id is not None:
        query = query.filter(LogEventRaw.correlated_to_id == target_id)  # type: ignore
    total = query.count()
    rows = query.offset(offset).limit(limit).all()
    return {
        "items": [
            {
                "id": row.id,
                "timestamp": row.timestamp,
                "event_type": row.parsed_event_type,
                "target_type": row.correlated_to_type,
                "target_id": row.correlated_to_id,
                "raw_line": row.raw_line,
            }
            for row in rows
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }
