from typing import Any

from sentarr.collectors.arr_client import ArrClient


def make_radarr_client(name: str, base_url: str, api_key: str) -> ArrClient:
    return ArrClient(name=name, base_url=base_url, api_key=api_key, client_type="radarr")


def normalize_movie(raw: dict[str, Any], source_id: int) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "external_id": str(raw.get("id")),
        "title": raw.get("title") or "Unknown",
        "year": raw.get("year"),
        "status": _status_from_movie(raw),
        "quality_profile": raw.get("qualityProfileId"),
        "root_folder": raw.get("rootFolderPath"),
        "download_id": _download_id(raw),
        "raw_data": raw,
    }


def _download_id(raw: dict[str, Any]) -> str | None:
    download_id = raw.get("downloadId")
    if isinstance(download_id, str) and download_id:
        return download_id.upper()
    return None


def _status_from_movie(raw: dict[str, Any]) -> str:
    if raw.get("hasFile"):
        return "imported"
    if raw.get("monitored"):
        return "monitored"
    return "unknown"
