from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.services.models import AlertEvent, LogLevel
from backend.services.storage import AlertRepository, LogRepository


class AlertManager:
    def __init__(self, log_repo: LogRepository, alert_repo: AlertRepository) -> None:
        self.log_repo = log_repo
        self.alert_repo = alert_repo
        self.error_threshold = 50
        self.window_minutes = 5

    def evaluate_error_frequency(self) -> AlertEvent | None:
        since = datetime.now(timezone.utc) - timedelta(minutes=self.window_minutes)
        errors = self.log_repo.count_errors_since(since)
        if errors <= self.error_threshold:
            return None

        alert = AlertEvent(
            id=str(uuid4()),
            rule_name="high_error_frequency",
            message=f"Error logs exceeded threshold: {errors} errors in {self.window_minutes} minutes",
            severity=LogLevel.ERROR,
        )
        self.alert_repo.add(alert)
        return alert
