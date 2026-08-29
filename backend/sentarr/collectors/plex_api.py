import logging
from typing import Any

from plexapi.server import PlexServer
from sqlmodel import Session, select

from sentarr.config import settings
from sentarr.health.propagate import (
    propagate_episode,
    propagate_movie,
    propagate_season,
    propagate_show,
)
from sentarr.models.plex import (
    Episode,
    EpisodeTask,
    EpisodeTaskType,
    Library,
    LibraryType,
    Movie,
    MovieTask,
    MovieTaskType,
    PlexServerConfig,
    Season,
    SeasonTask,
    SeasonTaskType,
    Show,
    ShowTask,
    ShowTaskType,
    TaskStatus,
)

logger = logging.getLogger(__name__)

# Graceful degradation state
_plex_degraded: bool = False
_plex_degraded_reason: str = ""
_plex_degraded_since: Any = None


def get_degraded_status() -> dict[str, Any] | None:
    """Return degradation info if Plex connection is in degraded mode, else None."""
    if not _plex_degraded:
        return None
    return {
        "degraded": True,
        "reason": _plex_degraded_reason,
        "since": _plex_degraded_since.isoformat() if _plex_degraded_since else None,
    }


def _set_degraded(reason: str) -> None:
    """Set degraded mode."""
    global _plex_degraded, _plex_degraded_reason, _plex_degraded_since
    from datetime import UTC, datetime

    if not _plex_degraded:
        _plex_degraded = True
        _plex_degraded_since = datetime.now(UTC)
    _plex_degraded_reason = reason
    logger.warning("Plex connection degraded: %s", reason)


def _clear_degraded() -> None:
    """Clear degraded mode after successful connection."""
    global _plex_degraded, _plex_degraded_reason, _plex_degraded_since
    if _plex_degraded:
        logger.info("Plex connection restored")
    _plex_degraded = False
    _plex_degraded_reason = ""
    _plex_degraded_since = None


def get_plex_server(url: str | None = None, token: str | None = None) -> PlexServer | None:
    """Connect to a Plex server. Falls back to settings when url/token not provided."""
    _url = url or settings.plex_url
    _token = token or settings.plex_token
    if not _token:
        logger.warning("PLEX_TOKEN is not set; cannot connect to Plex")
        _set_degraded("PLEX_TOKEN not configured")
        return None
    try:
        server = PlexServer(_url, _token)  # type: ignore[no-untyped-call]
        _clear_degraded()
        return server
    except Exception as exc:
        logger.exception("Failed to connect to Plex at %s", _url)
        _set_degraded(f"Connection failed: {exc}")
        return None


def _ensure_server_configs(session: Session) -> list[PlexServerConfig]:
    """Sync PLEX_SERVERS env config into the database and return active configs."""
    server_defs = settings.parsed_plex_servers
    if not server_defs:
        return []

    configs: list[PlexServerConfig] = []
    for srv in server_defs:
        name = srv.get("name", "default")
        existing = session.exec(
            select(PlexServerConfig).where(PlexServerConfig.name == name)
        ).first()
        if existing:
            existing.base_url = srv.get("url", existing.base_url)
            existing.token = srv.get("token", existing.token)
            existing.log_path = srv.get("log_path", existing.log_path)
            existing.is_active = srv.get("is_active", True)
            session.add(existing)
            configs.append(existing)
        else:
            cfg = PlexServerConfig(
                name=name,
                base_url=srv.get("url", ""),
                token=srv.get("token", ""),
                log_path=srv.get("log_path"),
                is_active=srv.get("is_active", True),
            )
            session.add(cfg)
            session.flush()
            configs.append(cfg)
    return [c for c in configs if c.is_active]


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
    """Sync libraries from all configured Plex servers."""
    server_configs = _ensure_server_configs(session)
    if not server_configs:
        # Legacy single-server fallback
        plex = get_plex_server()
        if plex:
            _sync_server_libraries(session, plex, plex_server_id=None)
        return

    for cfg in server_configs:
        plex = get_plex_server(url=cfg.base_url, token=cfg.token)
        if not plex:
            logger.warning("Skipping inactive/unreachable Plex server: %s", cfg.name)
            continue
        _sync_server_libraries(session, plex, plex_server_id=cfg.id)


def _sync_server_libraries(
    session: Session, server: PlexServer, plex_server_id: int | None
) -> None:
    """Sync libraries from a single Plex server connection."""
    sections: list[Any] = server.library.sections()
    for section in sections:
        section_type: str = section.type
        if section_type not in ("movie", "show"):
            continue
        if settings.libraries_filter_list and section.title not in settings.libraries_filter_list:
            continue

        existing = session.exec(
            select(Library).where(
                Library.plex_library_key == str(section.key),
                Library.plex_server_id == plex_server_id,
            )
        ).first()
        if existing:
            existing.name = section.title
            existing.type = LibraryType(section_type)
            existing.path = section.locations[0] if section.locations else None
            session.add(existing)
        else:
            library = Library(
                plex_server_id=plex_server_id,
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

    _propagate_all(session)


def _propagate_all(session: Session) -> None:
    """Recalculate overall_status and progress for all tracked items."""
    for movie in session.exec(select(Movie)).all():
        propagate_movie(session, movie)
    for show in session.exec(select(Show)).all():
        propagate_show(session, show)
    for season in session.exec(select(Season)).all():
        propagate_season(session, season)
    for episode in session.exec(select(Episode)).all():
        propagate_episode(session, episode)

    session.commit()


def _sync_movies(session: Session, library: Library, section: Any) -> None:
    videos: list[Any] = section.all()
    for video in videos:
        existing = session.exec(
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
        existing_show = session.exec(
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
            existing_season = session.exec(
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
                existing_episode = session.exec(
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
