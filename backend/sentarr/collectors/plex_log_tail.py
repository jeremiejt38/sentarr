import logging
from pathlib import Path

from sqlmodel import Session

from sentarr.collectors.plex_log_parser import parse_log_directory
from sentarr.config import settings

logger = logging.getLogger(__name__)


def tail_log(session: Session, path: Path | None = None, max_lines: int = 1000) -> int:
    """Backwards-compatible alias that ingests recent Plex log lines."""
    log_dir = path or (Path(settings.plex_log_path).parent if settings.plex_log_path else None)
    if not log_dir or not log_dir.exists():
        logger.warning("Plex log directory not found: %s", log_dir)
        return 0
    # parse_log_directory handles rotation and already-parsed deduplication will be added later.
    return parse_log_directory(session, log_dir)
