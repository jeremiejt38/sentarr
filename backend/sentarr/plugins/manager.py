"""Plugin discovery, validation and lifecycle management."""

from __future__ import annotations

import importlib.metadata
import logging
from typing import TYPE_CHECKING, Any

from sentarr.plugins.base import SentarrPlugin

if TYPE_CHECKING:
    from fastapi import FastAPI
    from sqlmodel import Session

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "sentarr_plugin"


class PluginManager:
    """Singleton-ish manager that owns the lifecycle of all plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, SentarrPlugin] = {}
        self._active: set[str] = set()

    # ---- Discovery & lifecycle -------------------------------------------

    def discover(self) -> list[str]:
        """Scan installed entry-points and instantiate plugin classes."""
        discovered: list[str] = []
        for ep in importlib.metadata.entry_points(group=ENTRY_POINT_GROUP):
            try:
                plugin_cls = ep.load()
                if not (isinstance(plugin_cls, type) and issubclass(plugin_cls, SentarrPlugin)):
                    logger.warning(
                        "Entry-point %s is not a SentarrPlugin subclass", ep.name
                    )
                    continue
                instance = plugin_cls()
                if not hasattr(instance, "meta") or not instance.meta:
                    logger.warning("Plugin %s has no 'meta' attribute, skipping", ep.name)
                    continue
                self._plugins[instance.meta.name] = instance
                discovered.append(instance.meta.name)
                logger.info("Discovered plugin: %s v%s", instance.meta.name, instance.meta.version)
            except Exception:
                logger.exception("Failed to load plugin entry-point %s", ep.name)
        return discovered

    def activate_all(self, app: FastAPI) -> None:
        """Activate every discovered plugin."""
        for name, plugin in self._plugins.items():
            try:
                self._activate(name, plugin, app)
            except Exception:
                logger.exception("Failed to activate plugin %s", name)

    def deactivate_all(self) -> None:
        """Deactivate every active plugin."""
        for name in list(self._active):
            plugin = self._plugins.get(name)
            if plugin:
                try:
                    plugin.on_deactivate()
                    logger.info("Deactivated plugin: %s", name)
                except Exception:
                    logger.exception("Error deactivating plugin %s", name)
            self._active.discard(name)

    def _activate(self, name: str, plugin: SentarrPlugin, app: FastAPI) -> None:
        plugin.on_activate(app)
        router = plugin.register_routes()
        if router:
            app.include_router(
                router,
                prefix=f"/api/v1/plugins/{name}",
                tags=[f"plugin:{name}"],
            )
        self._active.add(name)
        logger.info("Activated plugin: %s", name)

    # ---- Hook dispatch ----------------------------------------------------

    def dispatch_sync_complete(self, source: str, session: Session) -> None:
        for plugin in self._active_plugins():
            try:
                plugin.on_sync_complete(source, session)
            except Exception:
                logger.exception("Plugin %s error in on_sync_complete", plugin.meta.name)

    def dispatch_alert_created(self, alert_data: dict[str, Any], session: Session) -> None:
        for plugin in self._active_plugins():
            try:
                plugin.on_alert_created(alert_data, session)
            except Exception:
                logger.exception("Plugin %s error in on_alert_created", plugin.meta.name)

    def dispatch_alert_resolved(self, alert_data: dict[str, Any], session: Session) -> None:
        for plugin in self._active_plugins():
            try:
                plugin.on_alert_resolved(alert_data, session)
            except Exception:
                logger.exception("Plugin %s error in on_alert_resolved", plugin.meta.name)

    def dispatch_item_added(
        self, item_type: str, item_data: dict[str, Any], session: Session
    ) -> None:
        for plugin in self._active_plugins():
            try:
                plugin.on_item_added(item_type, item_data, session)
            except Exception:
                logger.exception("Plugin %s error in on_item_added", plugin.meta.name)

    def dispatch_item_status_changed(
        self,
        item_type: str,
        item_id: int,
        old_status: str,
        new_status: str,
        session: Session,
    ) -> None:
        for plugin in self._active_plugins():
            try:
                plugin.on_item_status_changed(item_type, item_id, old_status, new_status, session)
            except Exception:
                logger.exception("Plugin %s error in on_item_status_changed", plugin.meta.name)

    def dispatch_notification_send(
        self, title: str, body: str, event_type: str
    ) -> tuple[str, str]:
        """Let plugins modify notification content. Returns final (title, body)."""
        for plugin in self._active_plugins():
            try:
                result = plugin.on_notification_send(title, body, event_type)
                if result:
                    title = result.get("title", title)
                    body = result.get("body", body)
            except Exception:
                logger.exception("Plugin %s error in on_notification_send", plugin.meta.name)
        return title, body

    # ---- Introspection ----------------------------------------------------

    def list_plugins(self) -> list[dict[str, Any]]:
        """Return metadata for all discovered plugins."""
        return [
            {
                "name": p.meta.name,
                "version": p.meta.version,
                "description": p.meta.description,
                "author": p.meta.author,
                "url": p.meta.url,
                "active": p.meta.name in self._active,
            }
            for p in self._plugins.values()
        ]

    @property
    def plugin_count(self) -> int:
        return len(self._plugins)

    @property
    def active_count(self) -> int:
        return len(self._active)

    def _active_plugins(self) -> list[SentarrPlugin]:
        return [p for name, p in self._plugins.items() if name in self._active]


# Global singleton
plugin_manager = PluginManager()
