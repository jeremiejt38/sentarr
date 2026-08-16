import time

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram
from sqlalchemy import create_engine
from sqlmodel import Session, select

from sentarr.config import settings
from sentarr.models.arr import AcquisitionEvent, AcquisitionItem, Alert
from sentarr.models.plex import Episode, LogEventRaw, Movie, Show, TaskStatus


def build_registry() -> CollectorRegistry:
    registry = CollectorRegistry()
    _populate_from_db(registry)
    return registry


def _populate_from_db(registry: CollectorRegistry) -> None:
    engine = create_engine(str(settings.database_url))
    movies_total = Gauge("sentarr_movies_total", "Total number of movies", registry=registry)
    movies_status = Gauge(
        "sentarr_movies_status", "Movies by status", ["status"], registry=registry
    )
    shows_total = Gauge("sentarr_shows_total", "Total number of shows", registry=registry)
    shows_status = Gauge(
        "sentarr_shows_status", "Shows by status", ["status"], registry=registry
    )
    episodes_total = Gauge("sentarr_episodes_total", "Total number of episodes", registry=registry)
    episodes_status = Gauge(
        "sentarr_episodes_status", "Episodes by status", ["status"], registry=registry
    )
    active_alerts = Gauge("sentarr_active_alerts", "Number of active alerts", registry=registry)
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
    log_lines_unparsed = Gauge(
        "sentarr_log_lines_unparsed_total",
        "Total unparsed log lines",
        registry=registry,
    )
    # Histogram for poll duration — populated externally via observe_poll_duration()
    Histogram(
        "sentarr_plex_api_poll_duration_seconds",
        "Duration of Plex API polling",
        buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
        registry=registry,
    )

    with Session(engine) as session:
        movies = list(session.exec(select(Movie)).all())
        episodes = list(session.exec(select(Episode)).all())
        shows = list(session.exec(select(Show)).all())
        acquisition_items = list(session.exec(select(AcquisitionItem)).all())

        movies_total.set(len(movies))
        shows_total.set(len(shows))
        episodes_total.set(len(episodes))
        health_score.set(_compute_score(movies, episodes))
        health_threshold_warning.set(settings.health_threshold_warning)
        health_threshold_critical.set(settings.health_threshold_critical)

        # Per-status gauges
        for status in TaskStatus:
            movies_status.labels(status=status.value).set(
                sum(1 for m in movies if m.overall_status == status)
            )
            shows_status.labels(status=status.value).set(
                sum(1 for s in shows if s.overall_status == status)
            )
            episodes_status.labels(status=status.value).set(
                sum(1 for e in episodes if e.overall_status == status)
            )

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

        # Active alerts
        alert_count = len(
            list(
                session.exec(
                    select(Alert).where(Alert.resolved == False)  # noqa: E712
                ).all()
            )
        )
        active_alerts.set(alert_count)

        # Unparsed log lines
        unparsed = len(
            list(
                session.exec(
                    select(LogEventRaw).where(
                        LogEventRaw.parsed == False  # noqa: E712
                    )
                ).all()
            )
        )
        log_lines_unparsed.set(unparsed)


def _compute_score(movies: list[Movie], episodes: list[Episode]) -> int:
    total = len(movies) + len(episodes)
    if not total:
        return 100
    completed = sum(1 for item in movies + episodes if item.overall_status == TaskStatus.COMPLETED)
    return round((completed / total) * 100)


# --- Poll duration tracking (used by collectors) ---
_poll_start: float = 0.0


def start_poll_timer() -> None:
    global _poll_start
    _poll_start = time.monotonic()


def observe_poll_duration() -> float:
    duration = time.monotonic() - _poll_start
    return duration
