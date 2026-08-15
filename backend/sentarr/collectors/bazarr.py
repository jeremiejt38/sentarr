import logging
from typing import Any

import httpx

from sentarr.config import settings

logger = logging.getLogger(__name__)


class BazarrClient:
    """Read-only client for Bazarr API."""

    def __init__(self, base_url: str | None = None, api_key: str | None = None) -> None:
        self.base_url = (base_url or settings.bazarr_url or "").rstrip("/")
        self.api_key = api_key or settings.bazarr_api_key or ""
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"X-API-Key": self.api_key} if self.api_key else {},
            timeout=httpx.Timeout(30.0),
        )

    def _get(self, path: str) -> dict[str, Any]:
        try:
            response = self._client.get(path)
            response.raise_for_status()
            data = response.json()
            return data if isinstance(data, dict) else {}
        except httpx.HTTPStatusError as exc:
            logger.error("Bazarr %s returned %s", path, exc.response.status_code)
            return {}
        except httpx.RequestError as exc:
            logger.error("Bazarr request failed: %s", exc)
            return {}

    def get_episodes(self, series_id: int | None = None) -> list[dict[str, Any]]:
        params = {}
        if series_id is not None:
            params["seriesid"] = series_id
        response = self._client.get("/episodes", params=params)
        try:
            response.raise_for_status()
            data = response.json()
        except Exception:
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            payload = data.get("data")
            if isinstance(payload, list):
                return payload
        return []

    def get_series(self) -> list[dict[str, Any]]:
        data = self._get("/series")
        payload = data.get("data")
        if isinstance(payload, list):
            return payload
        return []

    def close(self) -> None:
        self._client.close()
