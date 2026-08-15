from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlmodel import Session, select

from sentarr.db import get_session
from sentarr.models.plex import Movie, MovieTask, TaskStatus
from sentarr.schemas.common import MovieSummary

router = APIRouter()


@router.get("")
async def list_movies(
    session: Session = Depends(get_session),
    library_id: int | None = Query(None),
    status: TaskStatus | None = Query(None),
    q: str | None = Query(None),
) -> list[MovieSummary]:
    stmt = select(Movie)
    if library_id is not None:
        stmt = stmt.where(Movie.library_id == library_id)
    if status is not None:
        stmt = stmt.where(Movie.overall_status == status)
    if q:
        stmt = stmt.where(text("title LIKE :pattern").bindparams(pattern=f"%{q}%"))
    movies = session.exec(stmt).all()
    return [
        MovieSummary(
            id=movie.id or 0,
            title=movie.title,
            year=movie.year,
            overall_status=movie.overall_status,
            progress_percent=movie.progress_percent,
            updated_at=movie.updated_at,
        )
        for movie in movies
    ]


@router.get("/{movie_id}")
async def get_movie(movie_id: int, session: Session = Depends(get_session)) -> dict[str, Any]:
    movie = session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return {
        "id": movie.id,
        "title": movie.title,
        "year": movie.year,
        "path": movie.path,
        "overall_status": movie.overall_status.value,
        "progress_percent": movie.progress_percent,
        "tasks": [
            {
                "type": task.task_type.value,
                "status": task.status.value,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "error_message": task.error_message,
            }
            for task in movie.tasks
        ],
        "updated_at": movie.updated_at,
    }


@router.get("/{movie_id}/timeline")
async def get_movie_timeline(
    movie_id: int, session: Session = Depends(get_session)
) -> dict[str, Any]:
    movie = session.get(Movie, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    tasks = session.exec(select(MovieTask).where(MovieTask.movie_id == movie_id)).all()
    return {
        "movie_id": movie.id,
        "title": movie.title,
        "steps": [
            {
                "key": task.task_type.value,
                "label": task.task_type.value,
                "status": task.status.value,
                "started_at": task.started_at,
                "completed_at": task.completed_at,
                "error_message": task.error_message,
            }
            for task in tasks
        ],
    }
