from prometheus_client import CollectorRegistry, Counter, Gauge
from sqlalchemy import create_engine
from sqlmodel import Session, select

from sentarr.config import settings
from sentarr.models.arr import AcquisitionEvent, AcquisitionItem
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
    health_threshold_warning = Gauge(
        "sentarr_health_threshold_warning", "Health score warning threshold", registry=registry
    )
    health_threshold_critical = Gauge(
        "sentarr_health_threshold_critical", "Health score critical threshold", registry=registry
    )
    tasks_total = Counter(
        "sentarr_tasks_total", "Total tasks by status", ["status", "item_type"], registry=registry
    )
    acquisition_items_total = Counter(
        "sentarr_acquisition_items_total",
        "Total acquisition items by status and client type",
        ["status", "client_type"],
        registry=registry,
    )
    acquisition_events_total = Counter(
        "sentarr_acquisition_events_total",
        "Total acquisition events by type",
        ["event_type"],
        registry=registry,
    )

    with Session(engine) as session:
        movies = list(session.exec(select(Movie)).all())
        episodes = list(session.exec(select(Episode)).all())
        acquisition_items = list(session.exec(select(AcquisitionItem)).all())
        movies_total.set(len(movies))
        episodes_total.set(len(episodes))
        health_score.set(_compute_score(movies, episodes))
        health_threshold_warning.set(settings.health_threshold_warning)
        health_threshold_critical.set(settings.health_threshold_critical)

        for status in TaskStatus:
            for item_type, items in (("movie", movies), ("episode", episodes)):
                count = sum(1 for item in items if item.overall_status == status)
                tasks_total.labels(status=status.value, item_type=item_type).inc(count)

        for item in acquisition_items:
            item_status = item.status if item.status else "unknown"
            client_type = item.client_type.value if item.client_type else "unknown"
            acquisition_items_total.labels(status=item_status, client_type=client_type).inc(1)

        for event in session.exec(select(AcquisitionEvent)).all():
            acquisition_events_total.labels(event_type=event.event_type).inc(1)


def _compute_score(movies: list[Movie], episodes: list[Episode]) -> int:
    total = len(movies) + len(episodes)
    if not total:
        return 100
    completed = sum(1 for item in movies + episodes if item.overall_status == TaskStatus.COMPLETED)
    return round((completed / total) * 100)
