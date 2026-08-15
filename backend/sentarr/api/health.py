from typing import Any

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from sentarr.db import get_session
from sentarr.models.plex import Episode, Movie, TaskStatus

router = APIRouter()


@router.get("")
async def health_score(session: Session = Depends(get_session)) -> dict[str, Any]:
    movies = session.exec(select(Movie)).all()
    episodes = session.exec(select(Episode)).all()

    total = len(movies) + len(episodes)
    completed = sum(
        1 for item in list(movies) + list(episodes) if item.overall_status == TaskStatus.COMPLETED
    )
    errors = sum(
        1 for item in list(movies) + list(episodes) if item.overall_status == TaskStatus.ERROR
    )

    score = round((completed / total) * 100) if total else 100
    return {
        "score": score,
        "total": total,
        "completed": completed,
        "errors": errors,
    }
