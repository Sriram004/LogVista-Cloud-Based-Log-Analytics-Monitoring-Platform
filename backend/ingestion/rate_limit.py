from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException


class SlidingWindowRateLimiter:
    def __init__(self, max_requests: int = 200, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window = timedelta(seconds=window_seconds)
        self.requests: dict[str, deque[datetime]] = defaultdict(deque)

    def check(self, client_id: str) -> None:
        now = datetime.now(timezone.utc)
        request_times = self.requests[client_id]
        while request_times and now - request_times[0] > self.window:
            request_times.popleft()
        if len(request_times) >= self.max_requests:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        request_times.append(now)
