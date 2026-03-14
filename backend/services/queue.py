from __future__ import annotations

import asyncio

from backend.services.models import IncomingLog


class InMemoryQueue:
    def __init__(self) -> None:
        self._queue: asyncio.Queue[IncomingLog] = asyncio.Queue()

    async def publish(self, item: IncomingLog) -> None:
        await self._queue.put(item)

    async def consume(self) -> IncomingLog:
        return await self._queue.get()

    def size(self) -> int:
        return self._queue.qsize()
