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
    tasks = movie.tasks
    return _calculate_breakdown(tasks)


def calculate_health_episode(episode: Episode) -> HealthBreakdown:
    tasks = episode.tasks
    return _calculate_breakdown(tasks)


def calculate_health_season(season: Season) -> HealthBreakdown:
    return _calculate_breakdown(season.tasks)


def calculate_health_show(show: Show) -> HealthBreakdown:
    total = 0
    completed = 0
    in_progress = 0
    error = 0
    pending = 0
    for season in show.seasons:
        breakdown = _calculate_breakdown(season.tasks)
        total += breakdown.total
        completed += breakdown.completed
        in_progress += breakdown.in_progress
        error += breakdown.error
        pending += breakdown.pending
    for task in show.tasks:
        status = task.status
        total += 1
        if status == TaskStatus.COMPLETED:
            completed += 1
        elif status == TaskStatus.IN_PROGRESS:
            in_progress += 1
        elif status == TaskStatus.ERROR:
            error += 1
        else:
            pending += 1
    score = int(completed * _task_weight(total)) if total else 100
    return HealthBreakdown(total, completed, in_progress, error, pending, score)


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
