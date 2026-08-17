from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlmodel import select

from sentarr.db import get_session
from sentarr.health.score import calculate_health_movie, calculate_health_show
from sentarr.models.plex import Episode, Movie, Season, Show
from sentarr.schemas.common import (
    EpisodeSummary,
    MovieSummary,
    SeasonSummary,
    ShowSummary,
    SummaryResponse,
)

router = APIRouter()


def _movie_summary(movie: Movie) -> MovieSummary:
    return MovieSummary(
        id=movie.id or 0,
        title=movie.title,
        year=movie.year,
        overall_status=movie.overall_status,
        progress_percent=movie.progress_percent,
        health_score=calculate_health_movie(movie).score,
        updated_at=movie.updated_at,
    )


def _episode_summary(episode: Episode) -> EpisodeSummary:
    return EpisodeSummary(
        id=episode.id or 0,
        episode_number=episode.episode_number,
        title=episode.title,
        overall_status=episode.overall_status,
        progress_percent=episode.progress_percent,
    )


def _season_summary(season: Season) -> SeasonSummary:
    return SeasonSummary(
        id=season.id or 0,
        season_number=season.season_number,
        overall_status=season.overall_status,
        progress_percent=season.progress_percent,
        episodes=[_episode_summary(ep) for ep in season.episodes] if season.episodes else None,
    )


def _show_summary(show: Show) -> ShowSummary:
    return ShowSummary(
        id=show.id or 0,
        title=show.title,
        year=show.year,
        overall_status=show.overall_status,
        progress_percent=show.progress_percent,
        health_score=calculate_health_show(show).score,
        seasons=[_season_summary(season) for season in show.seasons] if show.seasons else None,
    )


@router.get("", response_model=SummaryResponse)
async def summary(session: Session = Depends(get_session)) -> SummaryResponse:
    movies = session.exec(select(Movie)).all()  # type: ignore[attr-defined]
    shows = session.exec(select(Show)).all()  # type: ignore[attr-defined]

    return SummaryResponse(
        movies=[_movie_summary(movie) for movie in movies],
        shows=[_show_summary(show) for show in shows],
        total_movies=len(movies),
        total_shows=len(shows),
        movies_in_progress=sum(1 for m in movies if m.overall_status.value == "in_progress"),
        shows_in_progress=sum(1 for s in shows if s.overall_status.value == "in_progress"),
        errors=sum(1 for m in movies if m.overall_status.value == "error")
        + sum(1 for s in shows if s.overall_status.value == "error"),
    )
