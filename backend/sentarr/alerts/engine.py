from datetime import UTC, datetime, timedelta
from typing import cast

from sqlalchemy import text
from sqlmodel import Session, select

from sentarr.config import settings
from sentarr.models.arr import AcquisitionItem, Alert
from sentarr.notifications.engine import notify


class AlertEngine:
    """Generate alerts from acquisition and Plex data."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def evaluate(self) -> list[Alert]:
        created: list[Alert] = []
        created.extend(self._check_stalled_items())
        created.extend(self._check_failed_items())
        for alert in created:
            self.session.add(alert)
            self._notify(alert)
        self.session.commit()
        return created

    def _notify(self, alert: Alert) -> None:
        title = f"Sentarr alerte {alert.severity}"
        body = alert.message
        notify(title, body, alert.rule)

    def _check_stalled_items(self) -> list[Alert]:
        threshold = datetime.now(UTC) - timedelta(minutes=settings.stall_threshold_minutes)
        items = self.session.exec(
            select(AcquisitionItem).where(text("status IN ('grabbed', 'downloading')"))
        ).all()
        created: list[Alert] = []
        for item in items:
            if (
                item.updated_at
                and item.updated_at < threshold
                and not self._exists(cast(int, item.id), "acquisition_item", "stalled")
            ):
                created.append(
                    Alert(
                        target_type="acquisition_item",
                        target_id=cast(int, item.id),
                        severity="warning",
                        rule="stalled",
                        message=(
                            f"{item.title} est bloqué depuis plus de "
                            f"{settings.stall_threshold_minutes} minutes"
                        ),
                    )
                )
        return created

    def _check_failed_items(self) -> list[Alert]:
        items = self.session.exec(
            select(AcquisitionItem).where(AcquisitionItem.status == "failed")
        ).all()
        created: list[Alert] = []
        for item in items:
            if not self._exists(cast(int, item.id), "acquisition_item", "failed"):
                created.append(
                    Alert(
                        target_type="acquisition_item",
                        target_id=cast(int, item.id),
                        severity="error",
                        rule="failed",
                        message=f"{item.title} a échoué",
                    )
                )
        return created

    def _exists(self, target_id: int, target_type: str, rule: str) -> bool:
        existing = self.session.exec(
            select(Alert).where(
                Alert.target_id == target_id,
                Alert.target_type == target_type,
                Alert.rule == rule,
                Alert.resolved == False,  # noqa: E712
            )
        ).first()
        return existing is not None


def evaluate_alerts(session: Session) -> list[Alert]:
    return AlertEngine(session).evaluate()
