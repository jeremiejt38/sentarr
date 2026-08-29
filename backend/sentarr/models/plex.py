import enum
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel


def now_utc() -> datetime:
    return datetime.now(UTC)


if TYPE_CHECKING:
    pass


class PlexServerConfig(SQLModel, table=True):
    """Represents a Plex server instance tracked by Sentarr."""

    __tablename__ = "plex_servers"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True, sa_column_kwargs={"unique": True})
    base_url: str
    token: str
    log_path: str | None = Field(default=None, nullable=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    libraries: list["Library"] = Relationship(back_populates="server")


class LibraryType(enum.StrEnum):
    MOVIE = "movie"
    SHOW = "show"


class TaskStatus(enum.StrEnum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"
    NOT_APPLICABLE = "not_applicable"


class MovieTaskType(enum.StrEnum):
    SCAN = "scan"
    IDENTIFY = "identify"
    METADATA = "metadata"
    ARTWORK = "artwork"
    BIF = "bif"
    INTRO_MARKERS = "intro_markers"
    CHAPTER_MARKERS = "chapter_markers"
    STREAMS = "streams"
    OVERALL = "overall"


class ShowTaskType(enum.StrEnum):
    SCAN = "scan"
    IDENTIFY = "identify"
    METADATA = "metadata"
    ARTWORK = "artwork"
    OVERALL = "overall"


class SeasonTaskType(enum.StrEnum):
    SCAN = "scan"
    METADATA = "metadata"
    ARTWORK = "artwork"
    OVERALL = "overall"


class EpisodeTaskType(enum.StrEnum):
    SCAN = "scan"
    IDENTIFY = "identify"
    METADATA = "metadata"
    ARTWORK = "artwork"
    BIF = "bif"
    INTRO_MARKERS = "intro_markers"
    CHAPTER_MARKERS = "chapter_markers"
    STREAMS = "streams"
    OVERALL = "overall"


class Library(SQLModel, table=True):
    __tablename__ = "libraries"
    __table_args__ = (
        Index("ix_libraries_plex_library_key", "plex_library_key"),
        Index("ix_libraries_type", "type"),
    )

    id: int | None = Field(default=None, primary_key=True)
    plex_server_id: int | None = Field(
        default=None, nullable=True, foreign_key="plex_servers.id"
    )
    plex_library_key: str
    name: str
    type: LibraryType
    path: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    server: PlexServerConfig | None = Relationship(back_populates="libraries")
    movies: list["Movie"] = Relationship(back_populates="library")
    shows: list["Show"] = Relationship(back_populates="library")


class Movie(SQLModel, table=True):
    __tablename__ = "movies"
    __table_args__ = (
        Index("ix_movies_plex_rating_key", "plex_rating_key", unique=True),
        Index("ix_movies_library_id", "library_id"),
        Index("ix_movies_overall_status", "overall_status"),
    )

    id: int | None = Field(default=None, primary_key=True)
    library_id: int = Field(foreign_key="libraries.id")
    plex_rating_key: str
    title: str
    year: int | None = Field(default=None, nullable=True)
    path: str | None = Field(default=None, nullable=True)
    overall_status: TaskStatus = Field(default=TaskStatus.PENDING)
    progress_percent: int = Field(default=0, ge=0, le=100)
    added_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    library: Library = Relationship(back_populates="movies")
    tasks: list["MovieTask"] = Relationship(back_populates="movie")


class MovieTask(SQLModel, table=True):
    __tablename__ = "movie_tasks"
    __table_args__ = (
        Index("ix_movie_tasks_movie_id", "movie_id"),
        Index("ix_movie_tasks_task_type", "movie_id", "task_type", unique=True),
    )

    id: int | None = Field(default=None, primary_key=True)
    movie_id: int = Field(foreign_key="movies.id")
    task_type: MovieTaskType
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    started_at: datetime | None = Field(default=None, nullable=True)
    completed_at: datetime | None = Field(default=None, nullable=True)
    error_message: str | None = Field(default=None, nullable=True)
    updated_at: datetime = Field(default_factory=now_utc)

    movie: Movie = Relationship(back_populates="tasks")


class Show(SQLModel, table=True):
    __tablename__ = "shows"
    __table_args__ = (
        Index("ix_shows_plex_rating_key", "plex_rating_key", unique=True),
        Index("ix_shows_library_id", "library_id"),
        Index("ix_shows_overall_status", "overall_status"),
    )

    id: int | None = Field(default=None, primary_key=True)
    library_id: int = Field(foreign_key="libraries.id")
    plex_rating_key: str
    title: str
    year: int | None = Field(default=None, nullable=True)
    path: str | None = Field(default=None, nullable=True)
    overall_status: TaskStatus = Field(default=TaskStatus.PENDING)
    progress_percent: int = Field(default=0, ge=0, le=100)
    added_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)

    library: Library = Relationship(back_populates="shows")
    tasks: list["ShowTask"] = Relationship(back_populates="show")
    seasons: list["Season"] = Relationship(back_populates="show")


class ShowTask(SQLModel, table=True):
    __tablename__ = "show_tasks"
    __table_args__ = (
        Index("ix_show_tasks_show_id", "show_id"),
        Index("ix_show_tasks_task_type", "show_id", "task_type", unique=True),
    )

    id: int | None = Field(default=None, primary_key=True)
    show_id: int = Field(foreign_key="shows.id")
    task_type: ShowTaskType
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    started_at: datetime | None = Field(default=None, nullable=True)
    completed_at: datetime | None = Field(default=None, nullable=True)
    error_message: str | None = Field(default=None, nullable=True)
    updated_at: datetime = Field(default_factory=now_utc)

    show: Show = Relationship(back_populates="tasks")


class Season(SQLModel, table=True):
    __tablename__ = "seasons"
    __table_args__ = (
        Index("ix_seasons_plex_rating_key", "plex_rating_key", unique=True),
        Index("ix_seasons_show_id", "show_id"),
        Index("ix_seasons_overall_status", "overall_status"),
    )

    id: int | None = Field(default=None, primary_key=True)
    show_id: int = Field(foreign_key="shows.id")
    plex_rating_key: str
    season_number: int
    overall_status: TaskStatus = Field(default=TaskStatus.PENDING)
    progress_percent: int = Field(default=0, ge=0, le=100)
    updated_at: datetime = Field(default_factory=now_utc)

    show: Show = Relationship(back_populates="seasons")
    tasks: list["SeasonTask"] = Relationship(back_populates="season")
    episodes: list["Episode"] = Relationship(back_populates="season")


class SeasonTask(SQLModel, table=True):
    __tablename__ = "season_tasks"
    __table_args__ = (
        Index("ix_season_tasks_season_id", "season_id"),
        Index("ix_season_tasks_task_type", "season_id", "task_type", unique=True),
    )

    id: int | None = Field(default=None, primary_key=True)
    season_id: int = Field(foreign_key="seasons.id")
    task_type: SeasonTaskType
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    started_at: datetime | None = Field(default=None, nullable=True)
    completed_at: datetime | None = Field(default=None, nullable=True)
    error_message: str | None = Field(default=None, nullable=True)
    updated_at: datetime = Field(default_factory=now_utc)

    season: Season = Relationship(back_populates="tasks")


class Episode(SQLModel, table=True):
    __tablename__ = "episodes"
    __table_args__ = (
        Index("ix_episodes_plex_rating_key", "plex_rating_key", unique=True),
        Index("ix_episodes_season_id", "season_id"),
        Index("ix_episodes_overall_status", "overall_status"),
    )

    id: int | None = Field(default=None, primary_key=True)
    season_id: int = Field(foreign_key="seasons.id")
    plex_rating_key: str
    episode_number: int
    title: str | None = Field(default=None, nullable=True)
    path: str | None = Field(default=None, nullable=True)
    overall_status: TaskStatus = Field(default=TaskStatus.PENDING)
    progress_percent: int = Field(default=0, ge=0, le=100)
    updated_at: datetime = Field(default_factory=now_utc)

    season: Season = Relationship(back_populates="episodes")
    tasks: list["EpisodeTask"] = Relationship(back_populates="episode")


class EpisodeTask(SQLModel, table=True):
    __tablename__ = "episode_tasks"
    __table_args__ = (
        Index("ix_episode_tasks_episode_id", "episode_id"),
        Index("ix_episode_tasks_task_type", "episode_id", "task_type", unique=True),
    )

    id: int | None = Field(default=None, primary_key=True)
    episode_id: int = Field(foreign_key="episodes.id")
    task_type: EpisodeTaskType
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    started_at: datetime | None = Field(default=None, nullable=True)
    completed_at: datetime | None = Field(default=None, nullable=True)
    error_message: str | None = Field(default=None, nullable=True)
    updated_at: datetime = Field(default_factory=now_utc)

    episode: Episode = Relationship(back_populates="tasks")


class LogFileState(SQLModel, table=True):
    """Tracks the byte offset of the last Plex log parse to enable real tail."""

    __tablename__ = "log_file_states"

    file_path: str = Field(primary_key=True)
    last_offset: int = Field(default=0)
    last_size: int = Field(default=0)
    updated_at: datetime = Field(default_factory=now_utc)


class LogEventRaw(SQLModel, table=True):
    __tablename__ = "log_events_raw"
    __table_args__ = (
        Index("ix_log_events_raw_timestamp_parsed", "timestamp", "parsed"),
        Index("ix_log_events_raw_line_hash", "line_hash", unique=True),
    )

    id: int | None = Field(default=None, primary_key=True)
    raw_line: str
    line_hash: str
    timestamp: datetime | None = Field(default=None, nullable=True)
    parsed: bool = Field(default=False)
    parsed_event_type: str | None = Field(default=None, nullable=True)
    correlated_to_type: str | None = Field(default=None, nullable=True)
    correlated_to_id: int | None = Field(default=None, nullable=True)
    correlation_note: str | None = Field(default=None, nullable=True)
    created_at: datetime = Field(default_factory=now_utc)
