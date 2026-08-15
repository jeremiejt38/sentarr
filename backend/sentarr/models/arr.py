import enum
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Index
from sqlmodel import Field, SQLModel


def now_utc() -> datetime:
    return datetime.now(UTC)


class ArrClientType(enum.StrEnum):
    RADARR = "radarr"
    SONARR = "sonarr"


class ArrInstance(SQLModel, table=True):
    __tablename__ = "arr_instances"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    client_type: ArrClientType
    base_url: str
    api_key: str
    profile_label: str | None = None
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class AcquisitionItem(SQLModel, table=True):
    __tablename__ = "acquisition_items"
    __table_args__ = (
        Index("ix_acquisition_items_external_id", "source_id", "external_id"),
        Index("ix_acquisition_items_status", "status"),
        Index("ix_acquisition_items_correlated_to_type", "correlated_to_type"),
    )

    id: int | None = Field(default=None, primary_key=True)
    source_id: int = Field(foreign_key="arr_instances.id")
    external_id: str
    client_type: ArrClientType
    title: str
    year: int | None = None
    status: str = "unknown"
    quality_profile: str | None = None
    root_folder: str | None = None
    raw_data: str | None = None
    correlated_to_type: str | None = None  # movie | episode | show
    correlated_to_id: int | None = None
    downloaded_at: datetime | None = None
    imported_at: datetime | None = None
    created_at: datetime = Field(default_factory=now_utc)
    updated_at: datetime = Field(default_factory=now_utc)


class AcquisitionEvent(SQLModel, table=True):
    __tablename__ = "acquisition_events"
    __table_args__ = (Index("ix_acquisition_events_item_id", "item_id"),)

    id: int | None = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="acquisition_items.id")
    event_type: str  # grabbed, download_failed, download_imported, etc.
    message: str | None = None
    event_data: str | None = None  # JSON
    created_at: datetime = Field(default_factory=now_utc)


class Alert(SQLModel, table=True):
    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_item_type", "target_type", "target_id"),
        Index("ix_alerts_created_at", "created_at"),
    )

    id: int | None = Field(default=None, primary_key=True)
    target_type: str  # acquisition_item | movie | episode
    target_id: int
    severity: str  # info | warning | error
    rule: str
    message: str
    resolved: bool = Field(default=False)
    created_at: datetime = Field(default_factory=now_utc)
    resolved_at: datetime | None = Field(default=None, nullable=True)


def parse_arr_urls(raw: str, default_client_type: ArrClientType) -> list[dict[str, Any]]:
    """Parse a JSON list of *arr instance descriptors from settings."""
    import json

    try:
        items = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(items, list):
        return []
    return items
