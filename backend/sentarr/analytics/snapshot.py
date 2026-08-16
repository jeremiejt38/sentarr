import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import func
from sqlmodel import Session, delete, select

from sentarr.config import settings
from sentarr.models.analytics import AnalyticsSnapshot
from sentarr.models.plex import EpisodeTask, LogEventRaw, MovieTask, TaskStatus

logger = logging.getLogger(__name__)


def _bucket(now: datetime, granularity: str) -> str:
    if granularity == "hourly":
        return f"hourly:{now.strftime('%Y-%m-%dT%H')}"
    if granularity == "daily":
        return f"daily:{now.strftime('%Y-%m-%d')}"
    return f"{granularity}:{now.isoformat()}"


def take_snapshot(session: Session, now: datetime | None = None) -> None:
    now = now or datetime.now(UTC)
    for granularity in ("hourly", "daily"):
        bucket = _bucket(now, granularity)
        movie_total = _count_movie_tasks(session)
        movie_completed = _count_movie_tasks(session, TaskStatus.COMPLETED)
        movie_error = _count_movie_tasks(session, TaskStatus.ERROR)
        episode_total = _count_episode_tasks(session)
        episode_completed = _count_episode_tasks(session, TaskStatus.COMPLETED)
        episode_error = _count_episode_tasks(session, TaskStatus.ERROR)
        _upsert_metric(session, bucket, "movie_tasks_total", movie_total)
        _upsert_metric(session, bucket, "movie_tasks_completed", movie_completed)
        _upsert_metric(session, bucket, "movie_tasks_error", movie_error)
        _upsert_metric(session, bucket, "episode_tasks_total", episode_total)
        _upsert_metric(session, bucket, "episode_tasks_completed", episode_completed)
        _upsert_metric(session, bucket, "episode_tasks_error", episode_error)
        _upsert_metric(session, bucket, "log_events_total", _count_log_events(session))
    session.commit()
    logger.info("Analytics snapshot taken for %s", now.isoformat())


def _count_movie_tasks(session: Session, status: TaskStatus | None = None) -> int:
    stmt = select(func.count())
    stmt = stmt.select_from(MovieTask)
    if status is not None:
        stmt = stmt.where(MovieTask.status == status)
    return session.exec(stmt).one() or 0


def _count_episode_tasks(session: Session, status: TaskStatus | None = None) -> int:
    stmt = select(func.count())
    stmt = stmt.select_from(EpisodeTask)
    if status is not None:
        stmt = stmt.where(EpisodeTask.status == status)
    return session.exec(stmt).one() or 0


def _count_log_events(session: Session) -> int:
    return session.exec(select(func.count()).select_from(LogEventRaw)).one() or 0


def _upsert_metric(session: Session, bucket: str, metric: str, value: int) -> None:
    existing = session.exec(
        select(AnalyticsSnapshot).where(
            AnalyticsSnapshot.bucket == bucket,
            AnalyticsSnapshot.metric == metric,
        )
    ).first()
    if existing:
        existing.value = float(value)
        existing.created_at = datetime.now(UTC)
        session.add(existing)
    else:
        session.add(
            AnalyticsSnapshot(
                bucket=bucket,
                metric=metric,
                value=float(value),
            )
        )


def purge_old_log_events(session: Session, now: datetime | None = None) -> int:
    now = now or datetime.now(UTC)
    retention = timedelta(days=settings.history_retention_days)
    cutoff = now - retention
    result = session.exec(
        delete(LogEventRaw).where(LogEventRaw.created_at < cutoff)  # type: ignore[arg-type]
    )
    session.commit()
    logger.info("Purged %s old log events before %s", result.rowcount, cutoff.isoformat())
    return result.rowcount


def detect_anomalies(session: Session, metric: str, window_days: int = 7) -> list[dict[str, Any]]:
    now = datetime.now(UTC)
    since = now - timedelta(days=window_days)
    snapshots = session.exec(
        select(AnalyticsSnapshot)
        .where(AnalyticsSnapshot.metric == metric)
        .where(AnalyticsSnapshot.created_at >= since)
    ).all()
    if len(snapshots) < 2:
        return []
    values = [s.value for s in snapshots]
    mean = sum(values) / len(values)
    stddev = (sum((v - mean) ** 2 for v in values) / len(values)) ** 0.5
    anomalies = []
    for snapshot in snapshots:
        if stddev and abs(snapshot.value - mean) > 2 * stddev:
            anomalies.append(
                {
                    "bucket": snapshot.bucket,
                    "metric": snapshot.metric,
                    "value": snapshot.value,
                    "mean": round(mean, 2),
                    "stddev": round(stddev, 2),
                }
            )
    return anomalies
