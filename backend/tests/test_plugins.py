"""Tests for the plugin system."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from sentarr.main import app
from sentarr.plugins.base import PluginMeta, SentarrPlugin
from sentarr.plugins.manager import PluginManager

client = TestClient(app)


def test_plugins_list_endpoint() -> None:
    resp = client.get("/api/v1/plugins")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert "active" in data


def test_plugin_meta() -> None:
    meta = PluginMeta(
        name="test-plugin",
        version="1.0.0",
        description="A test plugin",
        author="Test Author",
    )
    assert meta.name == "test-plugin"
    assert meta.version == "1.0.0"


def test_plugin_manager_lifecycle() -> None:
    manager = PluginManager()

    class TestPlugin(SentarrPlugin):
        meta = PluginMeta(name="test", version="0.1.0")

        def on_activate(self, app: FastAPI) -> None:
            pass

    manager._plugins["test"] = TestPlugin()
    test_app = FastAPI()
    manager.activate_all(test_app)
    assert manager.active_count == 1
    assert manager.plugin_count == 1

    info = manager.list_plugins()
    assert len(info) == 1
    assert info[0]["name"] == "test"
    assert info[0]["active"] is True

    manager.deactivate_all()
    assert manager.active_count == 0


def test_plugin_manager_discover_empty() -> None:
    manager = PluginManager()
    discovered = manager.discover()
    # No plugins installed in test env, so list should be empty
    assert isinstance(discovered, list)


def test_plugin_hook_dispatch() -> None:
    manager = PluginManager()
    calls: list[str] = []

    class HookPlugin(SentarrPlugin):
        meta = PluginMeta(name="hook-test", version="0.1.0")

        def on_sync_complete(self, source: str, session: object) -> None:  # type: ignore[override]
            calls.append(f"sync:{source}")

    manager._plugins["hook-test"] = HookPlugin()
    manager._active.add("hook-test")
    manager.dispatch_sync_complete("plex", None)  # type: ignore[arg-type]
    assert calls == ["sync:plex"]
