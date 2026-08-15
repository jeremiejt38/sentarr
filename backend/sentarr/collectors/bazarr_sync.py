import logging
from datetime import UTC, datetime

from sqlmodel import Session, select

from sentarr.collectors.bazarr import BazarrClient
from sentarr.models.subtitles import SubtitleTrack

logger = logging.getLogger(__name__)


def sync_bazarr(session: Session) -> int:
    """Fetch subtitle tracks from Bazarr and store them."""
    client = BazarrClient()
    if not client.base_url:
        logger.info("Bazarr URL not configured, skipping sync")
        client.close()
        return 0

    try:
        episodes = client.get_episodes()
    except Exception:
        logger.exception("Failed to fetch Bazarr episodes")
        client.close()
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
                    )
                )
            updated += 1
    session.commit()
    client.close()
    return updated
