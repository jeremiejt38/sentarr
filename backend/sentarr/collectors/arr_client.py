import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class ArrClientError(Exception):
    pass


class ArrClient:
    """Read-only HTTP client for Radarr/Sonarr v3 API."""

    def __init__(self, name: str, base_url: str, api_key: str, client_type: str) -> None:
        self.name = name
        self.client_type = client_type
        self._client = httpx.Client(
            base_url=base_url.rstrip("/"),
            headers={"X-Api-Key": api_key},
            timeout=httpx.Timeout(30.0),
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        if method.upper() != "GET":
            raise ArrClientError(f"Only GET requests are allowed (got {method})")
        url = f"/api/v3{path}"
        try:
            response = self._client.get(url, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            logger.error("%s %s returned %s", self.name, url, exc.response.status_code)
            raise ArrClientError(f"HTTP {exc.response.status_code} from {self.name}") from exc
        except httpx.RequestError as exc:
            logger.error("Request to %s failed: %s", self.name, exc)
            raise ArrClientError(f"Request failed for {self.name}") from exc

    def get_health(self) -> Any:
        return self._request("GET", "/health")

    def get_queue(self, page_size: int = 1000) -> Any:
        return self._request("GET", "/queue", params={"pageSize": page_size})

    def get_history(self, page_size: int = 1000) -> Any:
        return self._request("GET", "/history", params={"pageSize": page_size})

    def get_quality_profiles(self) -> Any:
        return self._request("GET", "/qualityProfile")

    def get_root_folders(self) -> Any:
        return self._request("GET", "/rootFolder")

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "ArrClient":
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()
