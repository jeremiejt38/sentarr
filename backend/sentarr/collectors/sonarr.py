from typing import Any

from sentarr.collectors.arr_client import ArrClient


def make_sonarr_client(name: str, base_url: str, api_key: str) -> ArrClient:
    return ArrClient(name=name, base_url=base_url, api_key=api_key, client_type="sonarr")


def normalize_series(raw: dict[str, Any], source_id: int) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "external_id": str(raw.get("id")),
        "title": raw.get("title") or "Unknown",
        "year": raw.get("year"),
        "status": _status_from_series(raw),
        "quality_profile": raw.get("qualityProfileId"),
        "root_folder": raw.get("rootFolderPath"),
        "raw_data": raw,
    }


def normalize_episode(raw: dict[str, Any], source_id: int, series_id: int) -> dict[str, Any]:
    air_date = raw.get("airDate")
    return {
        "source_id": source_id,
        "external_id": f"{series_id}-{raw.get('id')}",
        "title": raw.get("title") or "Unknown",
        "year": int(air_date[:4]) if isinstance(air_date, str) and len(air_date) >= 4 else None,
        "status": _status_from_episode(raw),
        "quality_profile": None,
        "root_folder": None,
        "raw_data": raw,
    }


def _status_from_series(raw: dict[str, Any]) -> str:
    if raw.get("statistics", {}).get("episodeFileCount", 0) > 0:
        return "imported"
    if raw.get("monitored"):
        return "monitored"
    return "unknown"


def _status_from_episode(raw: dict[str, Any]) -> str:
    if raw.get("hasFile"):
        return "imported"
    if raw.get("monitored"):
        return "monitored"
    return "unknown"
