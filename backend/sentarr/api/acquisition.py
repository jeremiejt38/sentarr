from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlmodel import Session, select

from sentarr.db import get_session
from sentarr.models.arr import AcquisitionEvent, AcquisitionItem, ArrInstance

router = APIRouter()


@router.get("")
async def list_acquisition_items(
    session: Session = Depends(get_session),
    status: str | None = Query(None),
    source_id: int | None = Query(None),
    q: str | None = Query(None),
) -> list[dict[str, Any]]:
    stmt = select(AcquisitionItem)
    if status:
        stmt = stmt.where(AcquisitionItem.status == status)
    if source_id:
        stmt = stmt.where(AcquisitionItem.source_id == source_id)
    if q:
        stmt = stmt.where(text("title LIKE :pattern").bindparams(pattern=f"%{q}%"))
    items = session.exec(stmt).all()
    return [
        {
            "id": item.id,
            "title": item.title,
            "year": item.year,
            "status": item.status,
            "client_type": item.client_type.value,
            "source_id": item.source_id,
            "correlated_to_type": item.correlated_to_type,
            "correlated_to_id": item.correlated_to_id,
            "updated_at": item.updated_at,
        }
        for item in items
    ]


@router.get("/sources")
async def list_sources(session: Session = Depends(get_session)) -> list[dict[str, Any]]:
    instances = session.exec(select(ArrInstance).where(ArrInstance.is_active)).all()
    return [
        {
            "id": instance.id,
            "name": instance.name,
            "client_type": instance.client_type.value,
            "base_url": instance.base_url,
            "profile_label": instance.profile_label,
        }
        for instance in instances
    ]


@router.get("/{item_id}/timeline")
async def item_timeline(
    item_id: int, session: Session = Depends(get_session)
) -> list[dict[str, Any]]:
    item = session.get(AcquisitionItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Acquisition item not found")
    events = session.exec(
        select(AcquisitionEvent)
        .where(AcquisitionEvent.item_id == item_id)
        .order_by(AcquisitionEvent.occurred_at, AcquisitionEvent.id)  # type: ignore[arg-type]
    ).all()
    return [
        {
            "id": event.id,
            "event_type": event.event_type,
            "message": event.message,
            "occurred_at": event.occurred_at,
            "created_at": event.created_at,
        }
        for event in events
    ]
