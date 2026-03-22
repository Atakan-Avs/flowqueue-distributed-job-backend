# FlowQueue – Distributed & Event-Driven Job Processing System

FlowQueue is a production-style distributed job processing backend designed to simulate how modern scalable systems handle asynchronous workloads and inter-service communication.

The system combines **Celery-based task execution** with **Kafka-based event streaming**, creating a hybrid architecture that supports both background processing and event-driven workflows.

---

# Architecture Overview

FlowQueue follows a distributed and event-driven architecture:

Client  
↓  
FastAPI API  
↓  
Redis Queue (Celery)  
↓  
Celery Workers  
↓  
PostgreSQL Database  

AND  

Celery Workers  
↓  
Kafka Topic (`job-events`)  
↓  
Kafka Consumer  

---

# Core Concepts

### Task Execution Layer (Celery)

Celery is responsible for executing background jobs:

• Processes jobs asynchronously  
• Supports retries and failure handling  
• Uses Redis as broker  

---

### Event Layer (Kafka)

Kafka is used to publish system events:

• `job.completed`  
• `job.failed`  
• `job.dead_lettered`  

These events are consumed by independent consumers, enabling loosely coupled system design.

---

# Key Features

## Job Management API

Built with FastAPI, the API allows:

• Create jobs  
• List jobs  
• Retrieve job status  
• Retry failed jobs  
• Requeue dead letter jobs  

Endpoints:


POST /api/v1/jobs
GET /api/v1/jobs
GET /api/v1/jobs/{job_id}
POST /api/v1/jobs/{job_id}/retry
POST /api/v1/jobs/{job_id}/requeue
GET /api/v1/jobs/dead-letter


---

## Distributed Queue System

Uses **Redis + Celery**:

• Jobs are queued in Redis  
• Workers process jobs asynchronously  
• Supports horizontal scaling  

---

## Handler-Based Execution System

Jobs are processed using a handler architecture:

• EmailHandler  
• ReportHandler  
• WebhookHandler  

This decouples business logic from worker orchestration and makes the system easily extensible.

---

## Retry & Dead Letter Queue (DLQ)

• Jobs retry automatically (max 3 attempts)  
• Failed jobs are moved to DLQ  
• Prevents infinite retry loops  

---

## Job Attempt Tracking

Each execution attempt is recorded:

• attempt number  
• status (processing, success, failed)  
• execution timestamps  

This improves observability and debugging.

---

## Stuck Job Recovery

The system detects jobs stuck in `processing` state:

• Periodic scan via Celery Beat  
• Requeues jobs if retry limit not reached  
• Moves to DLQ if exhausted  

This ensures resilience against worker crashes.

---

## Idempotency Protection

Supports:


Idempotency-Key: <unique-key>


Prevents duplicate job creation on repeated requests.

---

## Distributed Locking

Redis-based locks ensure:


lock:job:{job_id}


A job cannot be processed by multiple workers simultaneously.

---

## Rate Limiting

Basic Redis-based rate limiting prevents API abuse.

---

# Observability

## Logging

Structured logs include:

• request_id  
• job_id  
• retry_count  
• status  

---

## Prometheus Metrics

Exposed metrics:


flowqueue_jobs_created_total
flowqueue_jobs_completed_total
flowqueue_jobs_failed_total
flowqueue_jobs_dead_letter_total
flowqueue_job_retries_total


---

## Grafana Dashboard

Visualizes:

• job throughput  
• failures  
• retries  
• DLQ events  

---

## Flower Monitoring


http://localhost:5555


Real-time Celery monitoring.

---

# Kafka Event System

## Producer

Workers publish events:

```json
{
  "event_type": "job.completed",
  "job_id": "...",
  "job_type": "report",
  "status": "completed",
  "timestamp": "..."
}
Consumer

Kafka consumer listens to job-events:

• Processes events independently
• Enables future services (analytics, notifications, audit)

Tech Stack
Backend

Python
FastAPI
SQLAlchemy

Queue & Workers

Redis
Celery

Event Streaming

Kafka (Confluent Client)

Database

PostgreSQL

Monitoring

Prometheus
Grafana
Flower

Infrastructure

Docker
Docker Compose

Testing

pytest

Running the Project

Clone repository:

git clone https://github.com/Atakan-Avs/flowqueue-distributed-job-backend

Enter directory:

cd flowqueue-distributed-job-backend

Start system:

docker compose up --build
Learning Outcomes

This project demonstrates:

• Distributed job processing
• Event-driven architecture
• Retry & DLQ patterns
• Kafka integration
• System observability
• Scalable backend design

Future Improvements

• Outbox pattern (guaranteed event delivery)
• Schema-based event validation
• Multi-consumer services
• OpenTelemetry tracing
• Advanced rate limiting

Author

Atakan Avsever

GitHub
https://github.com/Atakan-Avs