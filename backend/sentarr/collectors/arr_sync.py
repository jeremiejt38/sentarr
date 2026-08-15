import json
import logging
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
    now_utc,
    parse_arr_urls,
)

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
                _sync_instance(session, instance, client)
        except Exception:
            logger.exception("Failed to sync %s", instance.name)

    session.commit()


def _sync_instance(session: Session, instance: ArrInstance, client: ArrClient) -> None:
    queue = client.get_queue()
    history = client.get_history()

    records = queue.get("records", [])
    records.extend(history.get("records", []))

    for record in records:
        normalized = _normalize_record(record, instance)
        if not normalized:
            continue

        existing = session.exec(
            select(AcquisitionItem).where(
                AcquisitionItem.source_id == instance.id,
                AcquisitionItem.external_id == normalized["external_id"],
            )
        ).first()

        if existing:
            existing.status = normalized["status"]
            existing.updated_at = now_utc()
            session.add(existing)
        else:
            item = AcquisitionItem(
                source_id=instance.id,
                external_id=normalized["external_id"],
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
            _record_event(session, item, record.get("eventType", "unknown"), record)


def _normalize_record(record: dict[str, Any], instance: ArrInstance) -> dict[str, Any] | None:
    instance_id = cast(int, instance.id)
    if instance.client_type == ArrClientType.RADARR:
        return normalize_movie(record, instance_id)
    if instance.client_type == ArrClientType.SONARR:
        return normalize_series(record, instance_id)
    return None


def _record_event(
    session: Session,
    item: AcquisitionItem,
    event_type: str,
    event_data: dict[str, Any],
) -> None:
    session.add(
        AcquisitionEvent(
            item_id=item.id,
            event_type=event_type,
            message=event_data.get("statusMessages") or event_data.get("message"),
            event_data=json.dumps(event_data) if event_data else None,
        )
    )
