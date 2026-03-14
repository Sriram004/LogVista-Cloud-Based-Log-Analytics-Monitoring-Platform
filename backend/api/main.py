from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated

from fastapi import Depends, FastAPI, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from backend.alerts.rules import AlertManager
from backend.authentication.security import (
    authenticate_user,
    create_access_token,
    require_role,
    verify_ingestion_api_key,
)
from backend.ingestion.rate_limit import SlidingWindowRateLimiter
from backend.processing.engine import ProcessingEngine
from backend.services.models import IncomingLog, LogLevel, SearchQuery
from backend.services.queue import InMemoryQueue
from backend.services.realtime import ConnectionManager
from backend.services.storage import AlertRepository, LogRepository


class LoginRequest(BaseModel):
    username: str
    password: str


class AppState:
    def __init__(self) -> None:
        self.log_repo = LogRepository()
        self.alert_repo = AlertRepository()
        self.queue = InMemoryQueue()
        self.rate_limiter = SlidingWindowRateLimiter()
        self.alert_manager = AlertManager(self.log_repo, self.alert_repo)
        self.connections = ConnectionManager()
        self.worker_task: asyncio.Task | None = None


state = AppState()


async def processing_worker() -> None:
    while True:
        incoming = await state.queue.consume()
        processed = ProcessingEngine.process(incoming)
        state.log_repo.add(processed)
        alert = state.alert_manager.evaluate_error_frequency()
        await state.connections.broadcast({"type": "log", "payload": processed.model_dump(mode="json")})
        if alert:
            await state.connections.broadcast({"type": "alert", "payload": alert.model_dump(mode="json")})


@asynccontextmanager
async def lifespan(_: FastAPI):
    state.worker_task = asyncio.create_task(processing_worker())
    yield
    if state.worker_task:
        state.worker_task.cancel()


app = FastAPI(title="LogVista API", version="0.1.0", lifespan=lifespan)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "queue_depth": state.queue.size()}


@app.post("/api/v1/auth/login")
def login(payload: LoginRequest) -> dict:
    user = authenticate_user(payload.username, payload.password)
    if not user:
        return {"error": "Invalid credentials"}
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer", "role": user["role"]}


@app.post("/api/v1/ingest", status_code=202)
async def ingest_log(log: IncomingLog, client_id: Annotated[str, Depends(verify_ingestion_api_key)]) -> dict:
    state.rate_limiter.check(client_id)
    await state.queue.publish(log)
    return {"status": "accepted", "service": log.service}


@app.get("/api/v1/logs/search")
def search_logs(
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    service: str | None = Query(default=None),
    level: LogLevel | None = Query(default=None),
    keyword: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=500),
    _: Annotated[dict, Depends(require_role("Admin", "Developer", "Viewer"))] = None,
) -> dict:
    query = SearchQuery(
        start_time=start_time,
        end_time=end_time,
        service=service,
        level=level,
        keyword=keyword,
        page=page,
        page_size=page_size,
    )
    items, total = state.log_repo.query(query)
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [entry.model_dump(mode="json") for entry in items],
    }


@app.get("/api/v1/alerts")
def list_alerts(_: Annotated[dict, Depends(require_role("Admin", "Developer"))]) -> dict:
    return {"items": [a.model_dump(mode="json") for a in state.alert_repo.all()]}


@app.websocket("/api/v1/stream")
async def stream(websocket: WebSocket) -> None:
    await state.connections.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        state.connections.disconnect(websocket)
