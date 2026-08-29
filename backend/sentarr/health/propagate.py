"""Propagate task statuses up to parents and persist overall_status/progress."""

from datetime import UTC, datetime
from typing import Any

from sentarr.models.plex import Episode, Movie, Season, Show, TaskStatus


def _now() -> datetime:
    return datetime.now(UTC)


def _derive_status_from_values(statuses: list[TaskStatus]) -> TaskStatus:
    """Derive an item's overall status from a list of status values."""
    if not statuses:
        return TaskStatus.PENDING
    status_set = set(statuses)
    if TaskStatus.ERROR in status_set:
        return TaskStatus.ERROR
    if TaskStatus.IN_PROGRESS in status_set:
        return TaskStatus.IN_PROGRESS
    if all(s == TaskStatus.COMPLETED for s in status_set):
        return TaskStatus.COMPLETED
    if all(s == TaskStatus.NOT_APPLICABLE for s in status_set):
        return TaskStatus.NOT_APPLICABLE
    if TaskStatus.PENDING in status_set:
        return TaskStatus.PENDING
    if TaskStatus.COMPLETED in status_set:
        return TaskStatus.COMPLETED
    return TaskStatus.PENDING


def _progress_percent_from_values(statuses: list[TaskStatus]) -> int:
    """Weighted progress from a list of status values."""
    if not statuses:
        return 0
    applicable = [s for s in statuses if s != TaskStatus.NOT_APPLICABLE]
    if not applicable:
        return 100
    completed = sum(1 for s in applicable if s == TaskStatus.COMPLETED)
    return int((completed / len(applicable)) * 100)


def _task_statuses(tasks: Any) -> list[TaskStatus]:
    return [t.status for t in tasks]


def propagate_movie(session: Any, movie: Movie) -> None:
    """Recalculate and persist a movie's overall_status and progress_percent."""
    values = _task_statuses(movie.tasks)
    movie.overall_status = _derive_status_from_values(values)
    movie.progress_percent = _progress_percent_from_values(values)
    movie.updated_at = _now()
    session.add(movie)


def propagate_episode(session: Any, episode: Episode) -> None:
    """Recalculate and persist an episode's overall_status and progress_percent."""
    values = _task_statuses(episode.tasks)
    episode.overall_status = _derive_status_from_values(values)
    episode.progress_percent = _progress_percent_from_values(values)
    episode.updated_at = _now()
    session.add(episode)


def propagate_season(session: Any, season: Season) -> None:
    """Recalculate and persist a season's overall_status and progress_percent."""
    values = _task_statuses(season.tasks) + [
        e.overall_status for e in season.episodes
    ]
    season.overall_status = _derive_status_from_values(values)
    season.progress_percent = _progress_percent_from_values(values)
    season.updated_at = _now()
    session.add(season)


def propagate_show(session: Any, show: Show) -> None:
    """Recalculate and persist a show's overall_status and progress_percent."""
    values = _task_statuses(show.tasks) + [
        s.overall_status for s in show.seasons
    ]
    show.overall_status = _derive_status_from_values(values)
    show.progress_percent = _progress_percent_from_values(values)
    show.updated_at = _now()
    session.add(show)


def propagate_item(session: Any, item: Movie | Episode) -> None:
    """Propagate a single movie or episode, then roll up to parents if episode."""
    if isinstance(item, Movie):
        propagate_movie(session, item)
    elif isinstance(item, Episode):
        propagate_episode(session, item)
        session.flush()
        season = session.get(Season, item.season_id)
        if season:
            propagate_season(session, season)
            session.flush()
            show = session.get(Show, season.show_id)
            if show:
                propagate_show(session, show)
