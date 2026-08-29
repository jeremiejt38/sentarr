import json
import logging
from datetime import datetime
from typing import Any, cast

from sqlmodel import Session, select

from sentarr.collectors.arr_client import ArrClient
from sentarr.collectors.radarr import make_radarr_client, normalize_movie
from sentarr.collectors.sonarr import make_sonarr_client, normalize_series
from sentarr.config import settings
from sentarr.models.arr import (
    AcquisitionEvent,
    AcquisitionItem,
    ArrClientType,
    ArrInstance,
    QualityProfile,
    RootFolder,
    now_utc,
    parse_arr_urls,
)
from sentarr.models.plex import Episode, Movie

logger = logging.getLogger(__name__)


def get_arr_instances(session: Session) -> list[ArrInstance]:
    return list(session.exec(select(ArrInstance).where(ArrInstance.is_active)).all())


def sync_arr_instances(session: Session) -> None:
    """Ensure configured *arr instances are persisted in the database."""
    existing = {inst.name: inst for inst in session.exec(select(ArrInstance)).all()}

    for descriptor in parse_arr_urls(settings.radarr_urls, ArrClientType.RADARR):
        name = descriptor.get("name", "radarr")
        if name in existing:
            continue
        session.add(
            ArrInstance(
                name=name,
                client_type=ArrClientType.RADARR,
                base_url=descriptor.get("url", ""),
                api_key=_resolve_api_key(descriptor.get("api_key_env", "")),
                profile_label=descriptor.get("profile_label"),
            )
        )

    for descriptor in parse_arr_urls(settings.sonarr_urls, ArrClientType.SONARR):
        name = descriptor.get("name", "sonarr")
        if name in existing:
            continue
        session.add(
            ArrInstance(
                name=name,
                client_type=ArrClientType.SONARR,
                base_url=descriptor.get("url", ""),
                api_key=_resolve_api_key(descriptor.get("api_key_env", "")),
                profile_label=descriptor.get("profile_label"),
            )
        )

    session.commit()


def _resolve_api_key(env_var: str | None) -> str:
    import os

    if not env_var:
        return ""
    return os.environ.get(env_var, "")


def _make_client(instance: ArrInstance) -> ArrClient:
    if instance.client_type == ArrClientType.RADARR:
        return make_radarr_client(instance.name, instance.base_url, instance.api_key)
    return make_sonarr_client(instance.name, instance.base_url, instance.api_key)


def sync_acquisition(session: Session) -> None:
    sync_arr_instances(session)
    instances = get_arr_instances(session)

    for instance in instances:
        try:
            with _make_client(instance) as client:
                _sync_arr_metadata(session, instance, client)
                _sync_instance(session, instance, client)
        except Exception:
            logger.exception("Failed to sync %s", instance.name)

    _correlate_unmatched(session)
    session.commit()


def _sync_arr_metadata(
    session: Session, instance: ArrInstance, client: ArrClient
) -> None:
    """Sync quality profiles and root folders for an *arr instance."""
    try:
        profiles = client.get_quality_profiles()
    except Exception:
        logger.exception("Failed to fetch quality profiles from %s", instance.name)
        profiles = []

    if isinstance(profiles, list):
        existing = {
            (p.name, p.items)
            for p in session.exec(
                select(QualityProfile).where(QualityProfile.source_id == instance.id)
            ).all()
        }
        for raw in profiles:
            name = raw.get("name")
            if not name:
                continue
            items = json.dumps(raw.get("items"))
            if (name, items) in existing:
                continue
            session.add(
                QualityProfile(
                    source_id=instance.id,
                    external_id=str(raw.get("id", "")),
                    name=name,
                    items=items,
                )
            )

    try:
        roots = client.get_root_folders()
    except Exception:
        logger.exception("Failed to fetch root folders from %s", instance.name)
        roots = []

    if isinstance(roots, list):
        existing_paths = {
            p.path
            for p in session.exec(
                select(RootFolder).where(RootFolder.source_id == instance.id)
            ).all()
        }
        for raw in roots:
            path = raw.get("path")
            if not path:
                continue
            if path in existing_paths:
                continue
            session.add(
                RootFolder(
                    source_id=instance.id,
                    path=path,
                    accessible=raw.get("accessible", True),
                    free_space=raw.get("freeSpace"),
                )
            )


def _correlate_unmatched(session: Session) -> int:
    """Link acquisition items to existing Plex movies/episodes by normalized path."""
    correlated = 0
    movies = {m.path: m for m in session.exec(select(Movie)).all() if m.path}
    episodes = {e.path: e for e in session.exec(select(Episode)).all() if e.path}

    items = session.exec(
        select(AcquisitionItem).where(AcquisitionItem.correlated_to_type == None)  # noqa: E711
    ).all()

    for item in items:
        if item.correlated_to_type is not None or not item.root_folder:
            continue
        path = _extract_path(item.raw_data)
        if not path:
            continue
        if path in movies:
            item.correlated_to_type = "movie"
            item.correlated_to_id = movies[path].id
            correlated += 1
        elif path in episodes:
            item.correlated_to_type = "episode"
            item.correlated_to_id = episodes[path].id
            correlated += 1

    return correlated


def _extract_path(raw_data: str | None) -> str | None:
    if not raw_data:
        return None
    try:
        data = json.loads(raw_data)
    except json.JSONDecodeError:
        return None
    for key in ("movieFile", "episodeFile"):
        file_data = data.get(key)
        if isinstance(file_data, dict):
            rel_path = file_data.get("relativePath") or file_data.get("path")
            if isinstance(rel_path, str):
                return rel_path
    for key in ("path", "folderName"):
        value = data.get(key)
        if isinstance(value, str):
            return value
    return None


def _sync_instance(session: Session, instance: ArrInstance, client: ArrClient) -> None:
    queue = client.get_queue()
    history = client.get_history()

    records = list(queue.get("records", []))
    records.extend(history.get("records", []))

    for record in records:
        normalized = _normalize_record(record, instance)
        if not normalized:
            continue

        external_id = normalized["external_id"]
        existing = session.exec(
            select(AcquisitionItem).where(
                AcquisitionItem.source_id == instance.id,
                AcquisitionItem.external_id == external_id,
            )
        ).first()

        if existing:
            existing.status = _merge_status(existing.status, normalized["status"])
            existing.updated_at = now_utc()
            session.add(existing)
            item = existing
        else:
            item = AcquisitionItem(
                source_id=instance.id,
                external_id=external_id,
                client_type=instance.client_type,
                title=normalized["title"],
                year=normalized["year"],
                status=normalized["status"],
                quality_profile=str(normalized.get("quality_profile"))
                if normalized.get("quality_profile")
                else None,
                root_folder=normalized.get("root_folder"),
                raw_data=json.dumps(record),
            )
            session.add(item)
            session.flush()  # to obtain item.id before recording events

        _record_event(session, item, record)


def _normalize_record(record: dict[str, Any], instance: ArrInstance) -> dict[str, Any] | None:
    instance_id = cast(int, instance.id)
    if instance.client_type == ArrClientType.RADARR:
        return normalize_movie(record, instance_id)
    if instance.client_type == ArrClientType.SONARR:
        return normalize_series(record, instance_id)
    return None


def _merge_status(current: str, incoming: str) -> str:
    """Keep the most advanced status when merging queue and history records."""
    order = ["unknown", "monitored", "grabbed", "downloading", "imported", "failed"]
    try:
        current_index = order.index(current)
    except ValueError:
        current_index = -1
    try:
        incoming_index = order.index(incoming)
    except ValueError:
        incoming_index = -1
    return order[max(current_index, incoming_index)]


def _record_event(session: Session, item: AcquisitionItem, record: dict[str, Any]) -> None:
    event_type = record.get("eventType")
    if not event_type:
        event_type = _status_to_event_type(record.get("status"))

    occurred_at = _parse_occurred_at(record)
    if not event_type:
        return

    # Avoid exact duplicate events for the same item/type/time.
    existing = session.exec(
        select(AcquisitionEvent).where(
            AcquisitionEvent.item_id == item.id,
            AcquisitionEvent.event_type == event_type,
            AcquisitionEvent.occurred_at == occurred_at,
        )
    ).first()
    if existing:
        return

    session.add(
        AcquisitionEvent(
            item_id=item.id,
            event_type=event_type,
            message=record.get("statusMessages") or record.get("message"),
            event_data=json.dumps(record),
            occurred_at=occurred_at,
        )
    )


def _status_to_event_type(status: Any) -> str:
    if not isinstance(status, str):
        return "unknown"
    mapping = {
        "queued": "queued",
        "downloading": "downloading",
        "completed": "download_imported",
        "imported": "download_imported",
        "failed": "download_failed",
    }
    return mapping.get(status, status)


def _parse_occurred_at(record: dict[str, Any]) -> datetime | None:
    for key in ("date", "queueTime", "created", "added"):
        value = record.get(key)
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                continue
    return None
