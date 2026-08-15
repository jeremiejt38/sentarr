import logging
from typing import Any

from plexapi.server import PlexServer
from sqlalchemy.orm import Session
from sqlmodel import select

from sentarr.config import settings
from sentarr.models.plex import (
    Episode,
    EpisodeTask,
    EpisodeTaskType,
    Library,
    LibraryType,
    Movie,
    MovieTask,
    MovieTaskType,
    Season,
    SeasonTask,
    SeasonTaskType,
    Show,
    ShowTask,
    ShowTaskType,
    TaskStatus,
)

logger = logging.getLogger(__name__)


def get_plex_server() -> PlexServer | None:
    if not settings.plex_token:
        logger.warning("PLEX_TOKEN is not set; cannot connect to Plex")
        return None
    try:
        return PlexServer(settings.plex_url, settings.plex_token)  # type: ignore[no-untyped-call]
    except Exception:
        logger.exception("Failed to connect to Plex at %s", settings.plex_url)
        return None


def _task_status_from_video(video: Any) -> TaskStatus:
    """Estimate task status from a Plex video item."""
    if getattr(video, "isConverting", False):
        return TaskStatus.IN_PROGRESS
    return TaskStatus.COMPLETED


def _ensure_movie_tasks(session: Session, movie: Movie) -> None:
    existing = {task.task_type for task in movie.tasks}
    for task_type in MovieTaskType:
        if task_type in existing:
            continue
        task = MovieTask(movie_id=movie.id, task_type=task_type)
        session.add(task)


def _ensure_show_tasks(session: Session, show: Show) -> None:
    existing = {task.task_type for task in show.tasks}
    for task_type in ShowTaskType:
        if task_type in existing:
            continue
        task = ShowTask(show_id=show.id, task_type=task_type)
        session.add(task)


def _ensure_season_tasks(session: Session, season: Season) -> None:
    existing = {task.task_type for task in season.tasks}
    for task_type in SeasonTaskType:
        if task_type in existing:
            continue
        task = SeasonTask(season_id=season.id, task_type=task_type)
        session.add(task)


def _ensure_episode_tasks(session: Session, episode: Episode) -> None:
    existing = {task.task_type for task in episode.tasks}
    for task_type in EpisodeTaskType:
        if task_type in existing:
            continue
        task = EpisodeTask(episode_id=episode.id, task_type=task_type)
        session.add(task)


def sync_libraries(session: Session) -> None:
    server = get_plex_server()
    if not server:
        return

    sections: list[Any] = server.library.sections()
    for section in sections:
        section_type: str = section.type
        if section_type not in ("movie", "show"):
            continue
        if settings.libraries_filter_list and section.title not in settings.libraries_filter_list:
            continue

        existing = session.exec(  # type: ignore[attr-defined]
            select(Library).where(Library.plex_library_key == str(section.key))
        ).first()
        if existing:
            existing.name = section.title
            existing.type = LibraryType(section_type)
            existing.path = section.locations[0] if section.locations else None
            session.add(existing)
        else:
            library = Library(
                plex_library_key=str(section.key),
                name=section.title,
                type=LibraryType(section_type),
                path=section.locations[0] if section.locations else None,
            )
            session.add(library)
            session.flush()

        if section_type == "movie":
            _sync_movies(session, existing or library, section)
        else:
            _sync_shows(session, existing or library, section)

    session.commit()


def _sync_movies(session: Session, library: Library, section: Any) -> None:
    videos: list[Any] = section.all()
    for video in videos:
        existing = session.exec(  # type: ignore[attr-defined]
            select(Movie).where(Movie.plex_rating_key == str(video.ratingKey))
        ).first()
        status = _task_status_from_video(video)
        if existing:
            existing.title = video.title
            existing.year = video.year
            existing.path = video.locations[0] if video.locations else None
            existing.overall_status = status
            existing.progress_percent = 100 if status == TaskStatus.COMPLETED else 0
            session.add(existing)
        else:
            movie = Movie(
                library_id=library.id,
                plex_rating_key=str(video.ratingKey),
                title=video.title,
                year=video.year,
                path=video.locations[0] if video.locations else None,
                overall_status=status,
                progress_percent=100 if status == TaskStatus.COMPLETED else 0,
            )
            session.add(movie)
            session.flush()
            _ensure_movie_tasks(session, movie)


def _sync_shows(session: Session, library: Library, section: Any) -> None:
    show_videos: list[Any] = section.all()
    for show_video in show_videos:
        existing_show = session.exec(  # type: ignore[attr-defined]
            select(Show).where(Show.plex_rating_key == str(show_video.ratingKey))
        ).first()
        if existing_show:
            existing_show.title = show_video.title
            existing_show.year = getattr(show_video, "year", None)
            existing_show.path = show_video.locations[0] if show_video.locations else None
            session.add(existing_show)
            show = existing_show
        else:
            show = Show(
                library_id=library.id,
                plex_rating_key=str(show_video.ratingKey),
                title=show_video.title,
                year=getattr(show_video, "year", None),
                path=show_video.locations[0] if show_video.locations else None,
            )
            session.add(show)
            session.flush()
            _ensure_show_tasks(session, show)

        for season_video in show_video.seasons():
            existing_season = session.exec(  # type: ignore[attr-defined]
                select(Season).where(Season.plex_rating_key == str(season_video.ratingKey))
            ).first()
            if existing_season:
                existing_season.season_number = season_video.seasonNumber
                session.add(existing_season)
                season = existing_season
            else:
                season = Season(
                    show_id=show.id,
                    plex_rating_key=str(season_video.ratingKey),
                    season_number=season_video.seasonNumber,
                )
                session.add(season)
                session.flush()
                _ensure_season_tasks(session, season)

            for episode_video in season_video.episodes():
                existing_episode = session.exec(  # type: ignore[attr-defined]
                    select(Episode).where(Episode.plex_rating_key == str(episode_video.ratingKey))
                ).first()
                status = _task_status_from_video(episode_video)
                if existing_episode:
                    existing_episode.title = episode_video.title
                    existing_episode.path = (
                        episode_video.locations[0] if episode_video.locations else None
                    )
                    existing_episode.overall_status = status
                    existing_episode.progress_percent = 100 if status == TaskStatus.COMPLETED else 0
                    session.add(existing_episode)
                else:
                    episode = Episode(
                        season_id=season.id,
                        plex_rating_key=str(episode_video.ratingKey),
                        episode_number=episode_video.episodeNumber,
                        title=episode_video.title,
                        path=episode_video.locations[0] if episode_video.locations else None,
                        overall_status=status,
                        progress_percent=100 if status == TaskStatus.COMPLETED else 0,
                    )
                    session.add(episode)
                    session.flush()
                    _ensure_episode_tasks(session, episode)
