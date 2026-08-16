from datetime import UTC, datetime

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


def now_utc() -> datetime:
    return datetime.now(UTC)


class AnalyticsSnapshot(SQLModel, table=True):
    __tablename__ = "analytics_snapshots"
    __table_args__ = (
        Index("ix_analytics_snapshots_bucket", "bucket"),
        Index("ix_analytics_snapshots_created_at", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    bucket: str  # e.g. "hourly:2026-08-16T20" or "daily:2026-08-16"
    metric: str  # e.g. "movie_tasks_completed", "events_parsed"
    value: float
    dimensions: str | None = None  # JSON tags
    created_at: datetime = Field(default_factory=now_utc)
