from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class IncomingLog(BaseModel):
    timestamp: datetime
    service: str = Field(min_length=2, max_length=100)
    level: LogLevel
    message: str = Field(min_length=1, max_length=5000)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProcessedLog(IncomingLog):
    id: str
    normalized_level: LogLevel
    tags: list[str] = Field(default_factory=list)
    ingested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SearchQuery(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    service: str | None = None
    level: LogLevel | None = None
    keyword: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=500)


class AlertEvent(BaseModel):
    id: str
    rule_name: str
    message: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    severity: LogLevel = LogLevel.ERROR
