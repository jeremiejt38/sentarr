import logging
from pathlib import Path

from sqlalchemy.orm import Session

from sentarr.config import settings
from sentarr.models.plex import LogEventRaw

logger = logging.getLogger(__name__)


def tail_log(session: Session, path: Path | None = None, max_lines: int = 1000) -> int:
    log_path = path or (Path(settings.plex_log_path) if settings.plex_log_path else None)
    if not log_path or not log_path.exists():
        logger.warning("Plex log file not found: %s", log_path)
        return 0

    inserted = 0
    try:
        # Simple line-by-line ingestion. Production: use watchdog tailing.
        with log_path.open("r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        for raw_line in lines[-max_lines:]:
            session.add(LogEventRaw(raw_line=raw_line.rstrip("\n")))
            inserted += 1
        session.commit()
    except Exception:
        logger.exception("Failed to tail Plex log")
        session.rollback()
        return 0
    return inserted
