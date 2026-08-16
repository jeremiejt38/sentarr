"""Tests for multi-instance Bazarr/Prowlarr configuration parsing."""

import json

from sentarr.config import Settings


def test_parsed_plex_servers_empty() -> None:
    """When no PLEX_SERVERS and no PLEX_TOKEN, returns empty."""
    s = Settings(plex_token="", plex_servers="[]")
    assert s.parsed_plex_servers == []


def test_parsed_plex_servers_legacy_fallback() -> None:
    """When PLEX_SERVERS is empty but PLEX_TOKEN is set, falls back to single server."""
    s = Settings(
        plex_url="http://plex:32400",
        plex_token="my-token",
        plex_servers="[]",
    )
    servers = s.parsed_plex_servers
    assert len(servers) == 1
    assert servers[0]["name"] == "default"
    assert servers[0]["url"] == "http://plex:32400"
    assert servers[0]["token"] == "my-token"


def test_parsed_plex_servers_json() -> None:
    """When PLEX_SERVERS is set, returns parsed JSON."""
    cfg = json.dumps([
        {"name": "srv1", "url": "http://plex1:32400", "token": "t1"},
        {"name": "srv2", "url": "http://plex2:32400", "token": "t2"},
    ])
    s = Settings(plex_servers=cfg, plex_token="ignored")
    servers = s.parsed_plex_servers
    assert len(servers) == 2
    assert servers[0]["name"] == "srv1"
    assert servers[1]["name"] == "srv2"


def test_parsed_plex_servers_invalid_json() -> None:
    """Invalid JSON falls back to legacy."""
    s = Settings(plex_servers="not-json", plex_token="tok")
    servers = s.parsed_plex_servers
    assert len(servers) == 1
    assert servers[0]["name"] == "default"


def test_bazarr_instances_config() -> None:
    """Test that bazarr_instances can be parsed."""
    cfg = json.dumps([
        {"name": "bazarr-1", "url": "http://bazarr:6767", "api_key": "key1"},
    ])
    s = Settings(bazarr_instances=cfg)
    parsed = json.loads(s.bazarr_instances)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "bazarr-1"


def test_prowlarr_instances_config() -> None:
    """Test that prowlarr_instances can be parsed."""
    cfg = json.dumps([
        {"name": "prowlarr-1", "url": "http://prowlarr:9696", "api_key": "key1"},
    ])
    s = Settings(prowlarr_instances=cfg)
    parsed = json.loads(s.prowlarr_instances)
    assert len(parsed) == 1
    assert parsed[0]["name"] == "prowlarr-1"
