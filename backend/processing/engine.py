from __future__ import annotations

from uuid import uuid4

from backend.services.models import IncomingLog, LogLevel, ProcessedLog


class ProcessingEngine:
    @staticmethod
    def process(entry: IncomingLog) -> ProcessedLog:
        normalized_level = LogLevel(entry.level.upper())
        tags = [entry.service, normalized_level.value.lower()]
        if normalized_level in {LogLevel.ERROR, LogLevel.CRITICAL}:
            tags.append("requires_attention")
        return ProcessedLog(
            id=str(uuid4()),
            timestamp=entry.timestamp,
            service=entry.service.strip().lower(),
            level=entry.level,
            normalized_level=normalized_level,
            message=entry.message.strip(),
            metadata=entry.metadata,
            tags=tags,
        )
