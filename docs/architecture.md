# LogVista Architecture

## Components

1. **Log Ingestion Service** (`POST /api/v1/ingest`)
   - API key authentication (`X-API-Key`)
   - Request validation using Pydantic
   - Sliding-window rate limiting
2. **Message Queue Layer**
   - `InMemoryQueue` abstraction (replaceable with Kafka/RabbitMQ/Redis Streams)
3. **Log Processing Engine**
   - Parses and normalizes logs
   - Adds tags and severity markers
   - Stores processed logs
4. **Log Storage System**
   - In-memory repository for development (`LogRepository`)
   - Planned production adapters: OpenSearch/Elasticsearch/ClickHouse
5. **Log Search API** (`GET /api/v1/logs/search`)
   - Time range, service, level, keyword, pagination
6. **Real-time Dashboard Feed** (`/api/v1/stream` websocket)
   - Streams processed logs + alert events
7. **Alerting System**
   - Rule: high error frequency (>50 in 5 min)
   - Alert list endpoint (`GET /api/v1/alerts`)
8. **Authentication & Security**
   - JWT login for users
   - RBAC roles: Admin, Developer, Viewer
   - API key auth for ingestion clients

## Productionization Notes

- Deploy API and worker as separate containers.
- Replace `InMemoryQueue` with Kafka or Redis Streams.
- Replace `LogRepository` with OpenSearch index by day/time partition.
- Add Redis cache for common search queries.
- Add email/webhook integrations in `alerts` module.
