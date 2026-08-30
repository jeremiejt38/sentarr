from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlmodel import Session, select

from sentarr.db import get_session
from sentarr.models.arr import AcquisitionEvent, AcquisitionItem, ArrInstance
from sentarr.models.plex import Episode, EpisodeTask, Movie, MovieTask

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
            "download_id": item.download_id,
            "download_progress": item.download_progress,
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


# Mapping from acquisition event types to unified pipeline steps (1-6)
_ACQ_STEPS = [
    ("searched", "Recherché"),
    ("grabbed", "Release trouvée / Grab"),
    ("downloading", "Téléchargement"),
    ("download_complete", "Téléchargement terminé"),
    ("download_imported", "Import fichier"),
    ("imported", "Importé"),
]

# Mapping from Plex task types to unified pipeline steps (7-16)
_PLEX_STEPS = [
    ("detected", "Détecté par Plex"),
    ("scan", "Scanné"),
    ("identify", "Identifié"),
    ("metadata", "Métadonnées"),
    ("artwork", "Artworks"),
    ("bif", "Vignettes BIF"),
    ("intro_markers", "Marqueurs intro/générique"),
    ("chapter_markers", "Chapitres"),
    ("streams", "Flux audio/sous-titres"),
    ("overall", "Prêt"),
]


@router.get("/{item_id}/pipeline")
async def unified_pipeline(
    item_id: int, session: Session = Depends(get_session)
) -> dict[str, Any]:
    """Return the full 16-step unified pipeline for an acquisition item.

    Steps 1-6: acquisition events (Radarr/Sonarr).
    Steps 7-16: Plex processing tasks (from correlated movie/episode).
    """
    item = session.get(AcquisitionItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Acquisition item not found")

    # Fetch acquisition events
    events = session.exec(
        select(AcquisitionEvent)
        .where(AcquisitionEvent.item_id == item_id)
        .order_by(AcquisitionEvent.occurred_at, AcquisitionEvent.id)  # type: ignore[arg-type]
    ).all()
    event_types = {e.event_type for e in events}
    latest_by_type: dict[str, AcquisitionEvent] = {}
    for ev in events:
        existing = latest_by_type.get(ev.event_type)
        if not existing or (
            ev.occurred_at and existing.occurred_at and ev.occurred_at > existing.occurred_at
        ):
            latest_by_type[ev.event_type] = ev

    # Build acquisition steps (1-6)
    steps: list[dict[str, Any]] = []
    for step_key, label in _ACQ_STEPS:
        step_ev = latest_by_type.get(step_key)
        if step_ev:
            status = "error" if step_key == "failed" else "completed"
        elif "failed" in event_types:
            status = "not_applicable"
        elif event_types:
            status = "pending"
        else:
            status = "pending"
        steps.append({
            "step": len(steps) + 1,
            "key": step_key,
            "label": label,
            "phase": "acquisition",
            "status": status,
            "occurred_at": (
                step_ev.occurred_at.isoformat()
                if step_ev and step_ev.occurred_at
                else None
            ),
        })

    # Build Plex steps (7-16) from correlated item
    plex_tasks: list[MovieTask | EpisodeTask] = []
    if item.correlated_to_type == "movie" and item.correlated_to_id:
        movie = session.get(Movie, item.correlated_to_id)
        if movie:
            plex_tasks = list(
                session.exec(
                    select(MovieTask).where(MovieTask.movie_id == movie.id)
                ).all()
            )
    elif item.correlated_to_type == "episode" and item.correlated_to_id:
        episode = session.get(Episode, item.correlated_to_id)
        if episode:
            plex_tasks = list(
                session.exec(
                    select(EpisodeTask).where(EpisodeTask.episode_id == episode.id)
                ).all()
            )

    task_by_type = {t.task_type.value: t for t in plex_tasks}

    # "detected" is a synthetic step: Plex detected the file
    # We infer it from whether any Plex task has started
    any_plex_started = any(t.started_at for t in plex_tasks)
    detected_at = min(
        (t.started_at for t in plex_tasks if t.started_at), default=None
    )

    for step_key, label in _PLEX_STEPS:
        if step_key == "detected":
            if any_plex_started:
                status = "completed"
            elif "imported" in event_types:
                status = "in_progress"
            else:
                status = "pending"
            steps.append({
                "step": len(steps) + 1,
                "key": step_key,
                "label": label,
                "phase": "plex",
                "status": status,
                "occurred_at": detected_at.isoformat() if detected_at else None,
            })
            continue

        task = task_by_type.get(step_key)
        if task:
            status = task.status.value
            occurred = task.completed_at or task.started_at
        else:
            status = "pending" if item.correlated_to_id else "not_applicable"
            occurred = None
        steps.append({
            "step": len(steps) + 1,
            "key": step_key,
            "label": label,
            "phase": "plex",
            "status": status,
            "occurred_at": occurred.isoformat() if occurred else None,
        })

    # Compute import-to-detection delay
    import_event = latest_by_type.get("imported")
    import_to_detect_seconds = None
    if import_event and import_event.occurred_at and detected_at:
        import_to_detect_seconds = (detected_at - import_event.occurred_at).total_seconds()

    return {
        "item_id": item.id,
        "title": item.title,
        "correlated_to_type": item.correlated_to_type,
        "correlated_to_id": item.correlated_to_id,
        "steps": steps,
        "total_steps": len(steps),
        "import_to_detect_seconds": import_to_detect_seconds,
    }
