# FlowQueue – Distributed Job Processing Backend

FlowQueue is a production-grade distributed job processing system designed to demonstrate real-world backend engineering concepts such as asynchronous processing, event-driven architecture, reliability, and system design patterns.

---

## 🚀 Tech Stack

- **FastAPI** – API layer
- **PostgreSQL** – Persistent storage
- **Redis** – Queue & distributed lock
- **Celery** – Background workers
- **Kafka** – Event streaming
- **Docker Compose** – Infrastructure orchestration

---

## 🧠 System Architecture


Client
↓
FastAPI (API Layer)
↓
Redis Queue
↓
Celery Workers
↓
PostgreSQL (State + Outbox)
↓
Kafka (Event Streaming)
↓
Consumers


---

## ⚙️ Core Features

### 🔹 Asynchronous Job Processing
- Background job execution using Celery
- Priority-based queue system
- Distributed worker processing

### 🔹 Reliability & Fault Tolerance
- Retry mechanism with retry limits
- Dead Letter Queue (DLQ)
- Stuck job detection & recovery
- Automatic job requeueing

### 🔹 Distributed System Safety
- Idempotency keys (prevents duplicate job creation)
- Redis-based distributed locking (prevents double processing)
- Safe retry logic with failure tracking

### 🔹 Event-Driven Architecture
- Kafka integration for job lifecycle events
- Event-based system decoupling
- Consumer-based processing model

### 🔹 Data Consistency
- Transactional Outbox Pattern
- Guaranteed event delivery
- Duplicate event protection

---

## 🧩 Architecture Decisions

### 🔸 Service Layer Separation
Business logic is decoupled from the worker layer and centralized in a service layer:
- Improves testability
- Improves maintainability
- Enables scalable design

---

### 🔸 Plugin-Based Handler System
Job handlers are dynamically discovered and loaded:
- Open/Closed Principle (OCP)
- New job types can be added without modifying existing code
- Clean and extensible architecture

---

### 🔸 Outbox Pattern
Events are first written to the database and then published:
- Prevents data inconsistency
- Ensures reliable event delivery
- Handles Kafka failures safely

---

### 🔸 Dead Letter Queue (DLQ)
Failed jobs are moved to a separate state:
- Prevents infinite retry loops
- Enables manual inspection & recovery

---

### 🔸 Stuck Job Recovery
Jobs stuck in `processing` state are automatically:
- Recovered
- Requeued
- Or moved to dead letter

---

## 🔄 Job Lifecycle

1. Job created via API
2. Stored in PostgreSQL
3. Enqueued in Redis
4. Processed by Celery worker
5. Event written to Outbox table
6. Event published to Kafka
7. Consumer processes event

---

## 🔐 Authentication & Authorization

### ✔ JWT Authentication
- Access tokens (short-lived)
- Secure password hashing (bcrypt)

### ✔ Refresh Token System
- Secure storage (hashed tokens)
- Token expiration handling

### ✔ Refresh Token Rotation
- New token issued on each refresh
- Old tokens invalidated

### ✔ Reuse Detection
- Detects token reuse attacks
- Revokes compromised sessions

### ✔ Role-Based Access Control (RBAC)
- `admin` → full access
- `operator` → job management
- `viewer` → read-only

---

## 📦 API Endpoints

### 🔐 Auth
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### 📌 Jobs
- `POST /api/v1/jobs`
- `GET /api/v1/jobs`
- `GET /api/v1/jobs/{id}`
- `POST /api/v1/jobs/{id}/retry`
- `GET /api/v1/jobs/dead-letter`
- `POST /api/v1/jobs/{id}/requeue`

---

## 📊 Observability

- Structured logging
- Prometheus-style metrics
- Kafka event tracking
- Worker activity monitoring

---

## 🐳 Run Locally

```bash
docker compose up --build
🎯 Key Concepts Demonstrated
Distributed Systems
Event-Driven Architecture
Outbox Pattern
Retry & Dead Letter Queue
Idempotency
Distributed Locking
Plugin Architecture
Stuck Job Recovery
JWT Auth & Session Security
🚀 Why This Project?

This project simulates backend systems used in large-scale companies like:

Uber
Netflix
Amazon

It focuses on:

Scalability
Reliability
Fault tolerance
Production-ready backend design
🧭 Roadmap
Multi-tenant architecture (organization isolation)
Rate limiting & quotas
Advanced monitoring (Grafana dashboards)
Horizontal scaling improvements
👤 Author

Atakan Avsever

GitHub: https://github.com/Atakan-Avs
LinkedIn: https://linkedin.com/in/atakanavsever