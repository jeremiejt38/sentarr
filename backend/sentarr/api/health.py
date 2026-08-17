from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from sentarr.config import settings
from sentarr.db import get_session
from sentarr.models.arr import AcquisitionItem, Alert, ArrInstance
from sentarr.models.plex import Episode, Movie, Show, TaskStatus

router = APIRouter()


def _arr_instance_health(session: Session) -> list[dict[str, Any]]:
    """Check health of each *arr instance."""
    instances = session.exec(select(ArrInstance)).all()
    result: list[dict[str, Any]] = []
    for inst in instances:
        items_list = list(session.exec(
            select(AcquisitionItem).where(AcquisitionItem.source_id == inst.id)
        ).all())
        failed = sum(1 for i in items_list if i.status == "failed")
        stalled = sum(
            1 for i in items_list
            if i.status in ("grabbed", "downloading") and i.updated_at is not None
        )
        result.append({
            "id": inst.id,
            "name": inst.name,
            "client_type": inst.client_type.value if inst.client_type else None,
            "base_url": inst.base_url,
            "is_active": inst.is_active,
            "total_items": len(items_list),
            "failed_items": failed,
            "stalled_items": stalled,
            "status": "error" if failed > 0 else ("warning" if stalled > 0 else "ok"),
        })
    return result


def _import_to_detected_delays(session: Session) -> list[dict[str, Any]]:
    """Compute delay between last 'imported' event and Plex detection for correlated items."""
    from sentarr.models.arr import AcquisitionEvent

    correlated = session.exec(
        select(AcquisitionItem).where(AcquisitionItem.correlated_to_id.is_not(None))  # type: ignore
    ).all()
    delays: list[dict[str, Any]] = []
    for item in correlated[:20]:
        events = session.exec(
            select(AcquisitionEvent)
            .where(AcquisitionEvent.item_id == item.id)
            .order_by(AcquisitionEvent.occurred_at)  # type: ignore[arg-type]
        ).all()
        imported_at = None
        detected_at = None
        for ev in events:
            if ev.event_type == "imported":
                imported_at = ev.occurred_at
            if ev.event_type == "detected":
                detected_at = ev.occurred_at
        if imported_at and detected_at:
            delay_seconds = (detected_at - imported_at).total_seconds()
            delays.append({
                "item_id": item.id,
                "title": item.title,
                "imported_at": imported_at.isoformat() if imported_at else None,
                "detected_at": detected_at.isoformat() if detected_at else None,
                "delay_seconds": delay_seconds,
            })
    return delays


@router.get("")
async def health_score(session: Session = Depends(get_session)) -> dict[str, Any]:
    movies = list(session.exec(select(Movie)).all())
    shows = list(session.exec(select(Show)).all())
    episodes = list(session.exec(select(Episode)).all())

    total = len(movies) + len(episodes)
    completed = sum(
        1 for item in movies + episodes if item.overall_status == TaskStatus.COMPLETED
    )
    errors = sum(
        1 for item in movies + episodes if item.overall_status == TaskStatus.ERROR
    )
    in_progress = sum(
        1 for item in movies + episodes if item.overall_status == TaskStatus.IN_PROGRESS
    )

    score = round((completed / total) * 100) if total else 100

    # Active alerts
    active_alerts = list(
        session.exec(select(Alert).where(Alert.resolved == False)).all()  # noqa: E712
    )

    # *arr instance isolation
    arr_health = _arr_instance_health(session)

    # Plex degradation status
    try:
        from sentarr.collectors.plex_api import get_degraded_status

        plex_degraded = get_degraded_status()
    except (ImportError, AttributeError):
        plex_degraded = None

    return {
        "score": score,
        "total": total,
        "completed": completed,
        "in_progress": in_progress,
        "errors": errors,
        "total_movies": len(movies),
        "total_shows": len(shows),
        "total_episodes": len(episodes),
        "plex_degraded": plex_degraded,
        "active_alerts": [
            {
                "id": a.id,
                "severity": a.severity,
                "rule": a.rule,
                "message": a.message,
                "target_type": a.target_type,
                "target_id": a.target_id,
                "created_at": a.created_at,
            }
            for a in active_alerts
        ],
        "active_alerts_count": len(active_alerts),
        "arr_instances": arr_health,
        "thresholds": {
            "warning": settings.health_threshold_warning,
            "critical": settings.health_threshold_critical,
        },
        "alert_thresholds": {
            "searched": settings.alert_threshold_searched,
            "downloading": settings.alert_threshold_downloading,
            "importing": settings.alert_threshold_importing,
            "plex_overall": settings.alert_threshold_plex_overall,
        },
    }


@router.get("/delays")
async def import_to_detected(session: Session = Depends(get_session)) -> dict[str, Any]:
    delays = _import_to_detected_delays(session)
    avg_delay = (
        sum(d["delay_seconds"] for d in delays) / len(delays) if delays else 0
    )
    return {
        "items": delays,
        "count": len(delays),
        "avg_delay_seconds": round(avg_delay, 1),
    }


@router.get("/issues")
async def library_issues(session: Session = Depends(get_session)) -> dict[str, Any]:
    """Detect duplicates and misidentified items in Plex libraries."""
    from sentarr.health.anomalies import detect_all_issues

    return detect_all_issues(session)
