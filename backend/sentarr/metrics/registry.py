from prometheus_client import CollectorRegistry, Counter, Gauge
from sqlalchemy import create_engine
from sqlmodel import Session, select

from sentarr.config import settings
from sentarr.models.plex import Episode, Movie, TaskStatus


def build_registry() -> CollectorRegistry:
    registry = CollectorRegistry()
    _populate_from_db(registry)
    return registry


def _populate_from_db(registry: CollectorRegistry) -> None:
    engine = create_engine(str(settings.database_url))
    movies_total = Gauge("sentarr_movies_total", "Total number of movies", registry=registry)
    episodes_total = Gauge("sentarr_episodes_total", "Total number of episodes", registry=registry)
    health_score = Gauge("sentarr_health_score", "Overall health score 0-100", registry=registry)
    tasks_total = Counter(
        "sentarr_tasks_total", "Total tasks by status", ["status"], registry=registry
    )

    with Session(engine) as session:
        movies = list(session.exec(select(Movie)).all())
        episodes = list(session.exec(select(Episode)).all())
        movies_total.set(len(movies))
        episodes_total.set(len(episodes))
        health_score.set(_compute_score(movies, episodes))
        for status in TaskStatus:
            count = sum(1 for m in movies if m.overall_status == status)
            count += sum(1 for e in episodes if e.overall_status == status)
            tasks_total.labels(status=status.value).inc(count)


def _compute_score(movies: list[Movie], episodes: list[Episode]) -> int:
    total = len(movies) + len(episodes)
    if not total:
        return 100
    completed = sum(1 for item in movies + episodes if item.overall_status == TaskStatus.COMPLETED)
    return round((completed / total) * 100)
