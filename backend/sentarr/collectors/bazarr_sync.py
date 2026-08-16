import json
import logging
from datetime import UTC, datetime

from sqlmodel import Session, select

from sentarr.collectors.bazarr import BazarrClient
from sentarr.config import settings
from sentarr.models.subtitles import SubtitleTrack

logger = logging.getLogger(__name__)


def _get_bazarr_instances() -> list[dict[str, str]]:
    """Get Bazarr instances: multi-instance JSON or single-instance fallback."""
    try:
        instances = json.loads(settings.bazarr_instances)
    except (json.JSONDecodeError, AttributeError):
        instances = []
    if not isinstance(instances, list):
        instances = []
    if not instances and settings.bazarr_url:
        instances = [
            {
                "name": "default",
                "url": settings.bazarr_url,
                "api_key": settings.bazarr_api_key or "",
            }
        ]
    return instances


def sync_bazarr(session: Session) -> int:
    """Fetch subtitle tracks from all Bazarr instances and store them."""
    instances = _get_bazarr_instances()
    if not instances:
        logger.info("No Bazarr instances configured, skipping sync")
        return 0

    total = 0
    for inst in instances:
        url = inst.get("url", "")
        api_key = inst.get("api_key", "")
        if not url:
            continue
        client = BazarrClient(base_url=url, api_key=api_key)
        try:
            total += _sync_single_bazarr(session, client, source_name=inst.get("name", "default"))
        except Exception:
            logger.exception("Failed to sync Bazarr instance: %s", inst.get("name"))
        finally:
            client.close()
    return total


def _sync_single_bazarr(session: Session, client: BazarrClient, source_name: str) -> int:
    if not client.base_url:
        return 0

    try:
        episodes = client.get_episodes()
    except Exception:
        logger.exception("Failed to fetch Bazarr episodes from %s", source_name)
        return 0

    updated = 0
    for episode in episodes:
        episode_id = episode.get("sonarrEpisodeId")
        for sub in episode.get("subtitles", []):
            existing = session.exec(
                select(SubtitleTrack).where(
                    SubtitleTrack.episode_id == episode_id,
                    SubtitleTrack.language == sub.get("code2"),
                    SubtitleTrack.path == sub.get("path"),
                )
            ).first()
            if existing:
                existing.updated_at = datetime.now(UTC)
                session.add(existing)
            else:
                session.add(
                    SubtitleTrack(
                        episode_id=episode_id,
                        language=sub.get("code2", "unknown"),
                        hearing_impaired=sub.get("hearing_impaired", False),
                        forced=sub.get("forced", False),
                        path=sub.get("path"),
                        provider=sub.get("provider"),
                        source_name=source_name,
                    )
                )
            updated += 1
    session.commit()
    return updated
