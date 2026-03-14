# Workers

This directory is reserved for horizontally scalable background workers.

Current implementation runs an in-process async worker (`processing_worker`) inside the API service. In production, move the processing loop to dedicated worker containers and subscribe to Kafka/RabbitMQ/Redis Streams.
