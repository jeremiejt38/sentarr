from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlmodel import Session, select

from sentarr.db import get_session
from sentarr.models.plex import Movie, Show

router = APIRouter()


@router.get("")
async def search(
    session: Session = Depends(get_session),
    q: str = Query(..., min_length=1),
) -> dict[str, Any]:
    pattern = f"%{q}%"
    movies = session.exec(
        select(Movie).where(text("title LIKE :pattern_m").bindparams(pattern_m=pattern))
    ).all()
    shows = session.exec(
        select(Show).where(text("title LIKE :pattern_s").bindparams(pattern_s=pattern))
    ).all()
    return {
        "movies": [
            {
                "id": movie.id,
                "title": movie.title,
                "year": movie.year,
                "overall_status": movie.overall_status.value,
                "progress_percent": movie.progress_percent,
            }
            for movie in movies
        ],
        "shows": [
            {
                "id": show.id,
                "title": show.title,
                "year": show.year,
                "overall_status": show.overall_status.value,
                "progress_percent": show.progress_percent,
            }
            for show in shows
        ],
    }
