# FlowQueue – Distributed Job Processing Backend

FlowQueue is a production-style distributed job processing system built to demonstrate real-world backend engineering concepts such as asynchronous processing, reliability, and scalability.

---

## 🚀 Tech Stack

- **FastAPI** – API layer
- **PostgreSQL** – Persistent storage
- **Redis** – Queue & distributed lock
- **Celery** – Background workers
- **Kafka** – Event streaming
- **Docker Compose** – Infrastructure orchestration

---

## 🧠 System Design Overview

Client → FastAPI → Redis Queue → Celery Workers → PostgreSQL  
                                      ↓  
                                Kafka Events → Consumers

---

## ⚙️ Features

### 🔹 Job Processing
- Async job execution via Celery
- Retry mechanism with exponential backoff
- Dead Letter Queue support

### 🔹 Reliability
- Idempotency key support (prevents duplicate job creation)
- Distributed locking (prevents double processing)
- Duplicate event protection (consumer side)

### 🔹 Event-Driven Architecture
- Kafka producer for job lifecycle events
- Kafka consumer for processing events
- Outbox pattern for guaranteed event delivery

### 🔹 Data Consistency
- Transactional outbox pattern
- Audit logging via event consumers

### 🔹 Monitoring & Observability
- Structured logging
- Metrics (Prometheus-style counters)

---

## 🔄 Job Lifecycle

1. Job created via API
2. Stored in PostgreSQL
3. Published to Redis queue
4. Processed by Celery worker
5. Event emitted to Kafka
6. Consumer processes event (audit, logs, etc.)

---

## 🔒 Advanced Concepts Implemented

- Idempotency
- Distributed Locking
- Dead Letter Queue
- Retry Mechanisms
- Event-Driven Architecture
- Outbox Pattern
- Duplicate Event Protection

---

## 📦 API Endpoints (Examples)

- `POST /jobs` → Create job
- `GET /jobs` → List jobs
- `GET /jobs/{id}` → Job detail
- `POST /jobs/{id}/retry` → Retry job
- `GET /jobs/dead-letter` → Failed jobs
- `POST /jobs/{id}/requeue` → Requeue job

---

## 🐳 Run Locally

```bash
docker compose up --build
🎯 Why This Project?

This project simulates real-world backend systems used in companies like Uber, Netflix, and Amazon, focusing on:

Scalability
Fault tolerance
Distributed systems design
🧭 Next Steps
Authentication & Authorization (JWT)
Multi-tenant architecture
Rate limiting & quotas
Advanced monitoring (Grafana dashboards)
👤 Author

Atakan Avsever
GitHub: https://github.com/Atakan-Avs