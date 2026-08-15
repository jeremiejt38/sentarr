from datetime import datetime

from pydantic import BaseModel

from sentarr.models.plex import TaskStatus


class HealthResponse(BaseModel):
    status: str
    version: str


class MovieSummary(BaseModel):
    id: int
    title: str
    year: int | None
    overall_status: TaskStatus
    progress_percent: int
    updated_at: datetime


class EpisodeSummary(BaseModel):
    id: int
    episode_number: int
    title: str | None
    overall_status: TaskStatus
    progress_percent: int


class SeasonSummary(BaseModel):
    id: int
    season_number: int
    overall_status: TaskStatus
    progress_percent: int
    episodes: list[EpisodeSummary] | None = None


class ShowSummary(BaseModel):
    id: int
    title: str
    year: int | None
    overall_status: TaskStatus
    progress_percent: int
    seasons: list[SeasonSummary] | None = None


class SummaryResponse(BaseModel):
    movies: list[MovieSummary]
    shows: list[ShowSummary]
    total_movies: int
    total_shows: int
    movies_in_progress: int
    shows_in_progress: int
    errors: int
