# LogVista – Cloud-Based Log Analytics & Monitoring Platform

LogVista is a modular, cloud-ready log analytics platform starter that includes ingestion APIs, asynchronous processing, search, alerting, and real-time streaming.

## Implemented Features

- Log ingestion endpoint with JSON validation
- API key authentication + rate limiting for ingestion
- Async queue between ingestion and processing
- Processing engine for normalization and tagging
- Search API for time range/service/level/keyword filters
- JWT authentication and role-based authorization
- Alert rule for high error frequency
- WebSocket stream for real-time logs and alerts
- Container and Kubernetes starter manifests
- Unit tests and API health checks

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
uvicorn backend.api.main:app --reload
```

### Example Log Ingestion

```bash
curl -X POST http://127.0.0.1:8000/api/v1/ingest \
  -H "Content-Type: application/json" \
  -H "X-API-Key: demo-ingest-key" \
  -d '{
    "timestamp": "2026-03-14T12:00:00Z",
    "service": "auth-service",
    "level": "ERROR",
    "message": "Login failed",
    "metadata": {"user_id": "U123", "ip_address": "192.168.1.10"}
  }'
```

### JWT Login

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## Repository Structure

```text
logvista
├── frontend
├── backend
│   ├── api
│   ├── services
│   ├── ingestion
│   ├── processing
│   ├── alerts
│   └── authentication
├── workers
├── infrastructure
│   ├── docker
│   └── kubernetes
└── docs
```
