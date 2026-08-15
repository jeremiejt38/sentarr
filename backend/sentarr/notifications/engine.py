import json
import logging

import apprise

from sentarr.config import settings

logger = logging.getLogger(__name__)


class NotificationEngine:
    """Send notifications through Apprise."""

    def __init__(self) -> None:
        self.apprise = apprise.Apprise()
        self._load_channels()

    def _load_channels(self) -> None:
        try:
            channels = json.loads(settings.notification_channels or "[]")
        except json.JSONDecodeError:
            logger.warning("Invalid NOTIFICATION_CHANNELS JSON")
            return
        for channel in channels:
            url = channel.get("url")
            if url:
                self.apprise.add(url)

    def notify(self, title: str, body: str, event_type: str = "info") -> bool:
        if not self.apprise:
            return False
        try:
            result = self.apprise.notify(title=title, body=body)
            return result is True
        except Exception:
            logger.exception("Failed to send notification")
            return False


def notify(title: str, body: str, event_type: str = "info") -> bool:
    return NotificationEngine().notify(title, body, event_type)
