from unittest.mock import patch

import pytest

from sentarr.collectors.qbittorrent import QBittorrentClient, _map_status


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("uploading", "seeding"),
        ("stalledUP", "seeding"),
        ("forcedUP", "seeding"),
        ("downloading", "downloading"),
        ("stalledDL", "stalled"),
        ("metaDL", "downloading"),
        ("forcedDL", "downloading"),
        ("allocating", "downloading"),
        ("queuedDL", "queued"),
        ("queuedUP", "queued"),
        ("pausedDL", "paused"),
        ("pausedUP", "paused"),
        ("checkingUP", "checking"),
        ("checkingDL", "checking"),
        ("checkingResumeData", "checking"),
        ("moving", "moving"),
        ("error", "error"),
        ("missingFiles", "error"),
        ("unknown", "unknown"),
        ("foobar", "unknown"),
    ],
)
def test_map_status(state: str, expected: str) -> None:
    assert _map_status(state) == expected


def test_client_init_no_auth() -> None:
    with patch.object(QBittorrentClient, "_login"):
        client = QBittorrentClient("test", "http://localhost:8080")
    assert client._name == "test"
    assert client._base_url == "http://localhost:8080"
