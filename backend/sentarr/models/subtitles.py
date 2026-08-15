from datetime import UTC, datetime

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


def now_utc() -> datetime:
    return datetime.now(UTC)


class SubtitleTrack(SQLModel, table=True):
    __tablename__ = "subtitle_tracks"
    __table_args__ = (Index("ix_subtitle_tracks_episode_id", "episode_id"),)

    id: int | None = Field(default=None, primary_key=True)
    episode_id: int | None = None
    language: str
    hearing_impaired: bool = Field(default=False)
    forced: bool = Field(default=False)
    path: str | None = None
    provider: str | None = None
    downloaded_at: datetime | None = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)
