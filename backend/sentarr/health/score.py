from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from sentarr.models.plex import Episode, Movie, Season, Show, TaskStatus


class _StatusLike(Protocol):
    status: TaskStatus


@dataclass
class HealthBreakdown:
    total: int
    completed: int
    in_progress: int
    error: int
    pending: int
    score: int


def _task_weight(total: int) -> float:
    return 100 / total if total else 0.0


def calculate_health_movie(movie: Movie) -> HealthBreakdown:
    return _calculate_breakdown(movie.tasks)


def calculate_health_episode(episode: Episode) -> HealthBreakdown:
    return _calculate_breakdown(episode.tasks)


def calculate_health_season(season: Season) -> HealthBreakdown:
    return _aggregate_breakdowns(
        [_calculate_breakdown(episode.tasks) for episode in season.episodes]
        + [_calculate_breakdown(season.tasks)]
    )


def calculate_health_show(show: Show) -> HealthBreakdown:
    return _aggregate_breakdowns(
        [calculate_health_season(season) for season in show.seasons]
        + [_calculate_breakdown(show.tasks)]
    )


def _calculate_breakdown(tasks: Sequence[_StatusLike]) -> HealthBreakdown:
    total = len(tasks)
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
    error = sum(1 for t in tasks if t.status == TaskStatus.ERROR)
    pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
    not_applicable = sum(1 for t in tasks if t.status == TaskStatus.NOT_APPLICABLE)
    effective_total = total - not_applicable
    score = int(completed * _task_weight(effective_total)) if effective_total else 100
    return HealthBreakdown(total, completed, in_progress, error, pending, score)


def _aggregate_breakdowns(breakdowns: list[HealthBreakdown]) -> HealthBreakdown:
    total = sum(b.total for b in breakdowns)
    completed = sum(b.completed for b in breakdowns)
    in_progress = sum(b.in_progress for b in breakdowns)
    error = sum(b.error for b in breakdowns)
    pending = sum(b.pending for b in breakdowns)
    not_applicable = sum(
        b.total - b.completed - b.in_progress - b.error - b.pending
        for b in breakdowns
    )
    effective_total = total - not_applicable
    score = int(completed * _task_weight(effective_total)) if effective_total else 100
    return HealthBreakdown(total, completed, in_progress, error, pending, score)
