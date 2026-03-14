from __future__ import annotations

from collections import deque
from datetime import datetime

from backend.services.models import AlertEvent, ProcessedLog, SearchQuery


class LogRepository:
    def __init__(self, max_logs: int = 100_000) -> None:
        self._logs: deque[ProcessedLog] = deque(maxlen=max_logs)

    def add(self, log: ProcessedLog) -> None:
        self._logs.append(log)

    def all(self) -> list[ProcessedLog]:
        return list(self._logs)

    def query(self, request: SearchQuery) -> tuple[list[ProcessedLog], int]:
        items = self._logs
        filtered: list[ProcessedLog] = []
        for log in items:
            if request.start_time and log.timestamp < request.start_time:
                continue
            if request.end_time and log.timestamp > request.end_time:
                continue
            if request.service and log.service != request.service:
                continue
            if request.level and log.level != request.level:
                continue
            if request.keyword and request.keyword.lower() not in log.message.lower():
                continue
            filtered.append(log)

        total = len(filtered)
        start = (request.page - 1) * request.page_size
        end = start + request.page_size
        return filtered[start:end], total

    def count_errors_since(self, since: datetime) -> int:
        return sum(1 for log in self._logs if log.timestamp >= since and log.level in {"ERROR", "CRITICAL"})


class AlertRepository:
    def __init__(self, max_alerts: int = 10_000) -> None:
        self._alerts: deque[AlertEvent] = deque(maxlen=max_alerts)

    def add(self, alert: AlertEvent) -> None:
        self._alerts.appendleft(alert)

    def all(self) -> list[AlertEvent]:
        return list(self._alerts)
