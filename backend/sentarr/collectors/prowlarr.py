import logging
from typing import Any

import httpx

from sentarr.config import settings

logger = logging.getLogger(__name__)


class ProwlarrClient:
    """Read-only client for Prowlarr API."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = (base_url or settings.prowlarr_url or "").rstrip("/")
        self.api_key = api_key or settings.prowlarr_api_key or ""
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-Api-Key": self.api_key},
            timeout=httpx.Timeout(30.0),
        )

    def get_indexers(self) -> list[dict[str, Any]]:
        try:
            response = self._client.get("/api/v1/indexer")
            response.raise_for_status()
            data = response.json()
        except Exception:
            logger.exception("Failed to fetch Prowlarr indexers")
            return []
        if isinstance(data, list):
            return data
        return []

    def get_indexer_status(self) -> list[dict[str, Any]]:
        try:
            response = self._client.get("/api/v1/indexerstatus")
            response.raise_for_status()
            data = response.json()
        except Exception:
            logger.exception("Failed to fetch Prowlarr indexer status")
            return []
        if isinstance(data, list):
            return data
        return []

    def close(self) -> None:
        self._client.close()
