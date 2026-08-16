"""Base class and hook definitions for Sentarr plugins."""

from __future__ import annotations

from abc import ABC
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import APIRouter, FastAPI
    from sqlmodel import Session


class PluginMeta:
    """Metadata descriptor for a plugin."""

    def __init__(
        self,
        name: str,
        version: str = "0.1.0",
        description: str = "",
        author: str = "",
        url: str = "",
        min_sentarr_version: str = "0.5.0",
    ) -> None:
        self.name = name
        self.version = version
        self.description = description
        self.author = author
        self.url = url
        self.min_sentarr_version = min_sentarr_version


class SentarrPlugin(ABC):
    """Base class every plugin must subclass.

    Override any lifecycle/hook method you need.  Methods you don't override are
    no-ops by default so a minimal plugin only needs ``meta`` + ``on_activate``.
    """

    meta: PluginMeta

    # ---- Lifecycle ---------------------------------------------------------

    def on_activate(self, app: FastAPI) -> None:
        """Called once at startup after the plugin is discovered and validated."""

    def on_deactivate(self) -> None:
        """Called when the plugin is disabled or the app shuts down."""

    def register_routes(self) -> APIRouter | None:
        """Return a FastAPI router to be mounted under ``/api/v1/plugins/{name}/``.

        Return ``None`` to skip route registration.
        """
        return None

    def register_scheduled_jobs(self) -> list[dict[str, Any]]:
        """Return a list of APScheduler job dicts to register.

        Each dict should have keys compatible with ``scheduler.add_job()``:
        ``func``, ``trigger``, ``seconds``/``minutes``, ``id``, etc.

        Example::

            return [{
                "func": self.my_periodic_task,
                "trigger": "interval",
                "minutes": 5,
                "id": f"plugin_{self.meta.name}_task",
            }]
        """
        return []

    # ---- Hooks (called by Sentarr core at specific points) -----------------

    def on_sync_complete(self, source: str, session: Session) -> None:
        """Fired after a successful sync (plex, arr, bazarr, prowlarr)."""

    def on_alert_created(self, alert_data: dict[str, Any], session: Session) -> None:
        """Fired when a new alert is created."""

    def on_alert_resolved(self, alert_data: dict[str, Any], session: Session) -> None:
        """Fired when an alert is resolved."""

    def on_item_added(self, item_type: str, item_data: dict[str, Any], session: Session) -> None:
        """Fired when a new movie/show/episode is discovered."""

    def on_item_status_changed(
        self,
        item_type: str,
        item_id: int,
        old_status: str,
        new_status: str,
        session: Session,
    ) -> None:
        """Fired when an item's overall_status changes."""

    def on_notification_send(
        self, title: str, body: str, event_type: str
    ) -> dict[str, Any] | None:
        """Intercept notifications before they are sent via Apprise.

        Return a dict with ``title``/``body`` overrides, or ``None`` to skip
        this plugin's modification.
        """
        return None
