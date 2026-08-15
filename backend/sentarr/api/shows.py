from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlmodel import select

from sentarr.db import get_session
from sentarr.models.plex import Episode, Season, Show, ShowTask, TaskStatus
from sentarr.schemas.common import ShowSummary

router = APIRouter()


def _episode_detail(episode: Episode) -> dict[str, Any]:
    return {
        "id": episode.id,
        "episode_number": episode.episode_number,
        "title": episode.title,
        "overall_status": episode.overall_status.value,
        "progress_percent": episode.progress_percent,
        "tasks": [
            {
                "type": task.task_type.value,
                "status": task.status.value,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "error_message": task.error_message,
            }
            for task in episode.tasks
        ],
    }


def _season_detail(season: Season) -> dict[str, Any]:
    return {
        "id": season.id,
        "season_number": season.season_number,
        "overall_status": season.overall_status.value,
        "progress_percent": season.progress_percent,
        "tasks": [
            {
                "type": task.task_type.value,
                "status": task.status.value,
            }
            for task in season.tasks
        ],
        "episodes": [_episode_detail(episode) for episode in season.episodes],
    }


@router.get("")
async def list_shows(
    session: Session = Depends(get_session),
    library_id: int | None = Query(None),
    status: TaskStatus | None = Query(None),
    q: str | None = Query(None),
) -> list[ShowSummary]:
    stmt = select(Show)
    if library_id is not None:
        stmt = stmt.where(Show.library_id == library_id)
    if status is not None:
        stmt = stmt.where(Show.overall_status == status)
    if q:
        stmt = stmt.where(text("title LIKE :pattern").bindparams(pattern=f"%{q}%"))
    shows = session.exec(stmt).all()  # type: ignore
    return [
        ShowSummary(
            id=show.id or 0,
            title=show.title,
            year=show.year,
            overall_status=show.overall_status,
            progress_percent=show.progress_percent,
        )
        for show in shows
    ]


@router.get("/{show_id}")
async def get_show(show_id: int, session: Session = Depends(get_session)) -> dict[str, Any]:
    show = session.get(Show, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    return {
        "id": show.id,
        "title": show.title,
        "year": show.year,
        "overall_status": show.overall_status.value,
        "progress_percent": show.progress_percent,
        "tasks": [
            {
                "type": task.task_type.value,
                "status": task.status.value,
            }
            for task in show.tasks
        ],
        "seasons": [_season_detail(season) for season in show.seasons],
    }


@router.get("/{show_id}/timeline")
async def get_show_timeline(
    show_id: int, session: Session = Depends(get_session)
) -> dict[str, Any]:
    show = session.get(Show, show_id)
    if not show:
        raise HTTPException(status_code=404, detail="Show not found")
    show_tasks = session.exec(select(ShowTask).where(ShowTask.show_id == show_id)).all()  # type: ignore
    return {
        "show_id": show.id,
        "title": show.title,
        "steps": [
            {
                "key": task.task_type.value,
                "label": task.task_type.value,
                "status": task.status.value,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "error_message": task.error_message,
            }
            for task in show_tasks
        ],
    }


@router.get("/{show_id}/seasons/{season_id}")
async def get_season(
    show_id: int, season_id: int, session: Session = Depends(get_session)
) -> dict[str, Any]:
    season = session.get(Season, season_id)
    if not season or season.show_id != show_id:
        raise HTTPException(status_code=404, detail="Season not found")
    return _season_detail(season)


@router.get("/{show_id}/seasons/{season_id}/episodes/{episode_id}")
async def get_episode(
    show_id: int, season_id: int, episode_id: int, session: Session = Depends(get_session)
) -> dict[str, Any]:
    episode = session.get(Episode, episode_id)
    if not episode or episode.season_id != season_id:
        raise HTTPException(status_code=404, detail="Episode not found")
    return _episode_detail(episode)
