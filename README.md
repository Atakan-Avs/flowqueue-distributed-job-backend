# FlowQueue – Distributed Job Processing Backend

FlowQueue is a production-grade distributed job processing system designed to demonstrate real-world backend engineering concepts such as asynchronous processing, event-driven architecture, reliability, and secure authentication.

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
- Asynchronous job execution via Celery
- Retry mechanism with exponential backoff
- Dead Letter Queue (DLQ) support

### 🔹 Reliability
- Idempotency key support (prevents duplicate job creation)
- Distributed locking using Redis (prevents double processing)
- Duplicate event protection on consumer side

### 🔹 Event-Driven Architecture
- Kafka producer for job lifecycle events
- Kafka consumer for processing events
- Transactional Outbox Pattern for reliable event publishing

### 🔹 Data Consistency
- Guaranteed event delivery via outbox pattern
- Event-based audit logging

### 🔹 Monitoring & Observability
- Structured logging
- Prometheus-style metrics
- System behavior visibility

---

## 🔐 Authentication & Authorization

FlowQueue includes a **production-grade authentication system**:

### ✔ JWT Authentication
- Access tokens (short-lived)
- Secure password hashing (bcrypt)

### ✔ Refresh Token System
- Refresh tokens stored securely in the database (hashed)
- Token expiration management

### ✔ Refresh Token Rotation
- New refresh token issued on each refresh
- Old tokens automatically invalidated

### ✔ Reuse Detection (Security)
- Reuse of revoked tokens is detected
- System treats reused tokens as potential security threats

### ✔ Logout & Session Control
- Refresh tokens revoked on logout
- Session invalidation supported

### ✔ Role-Based Access Control (RBAC)
- `admin` → full access
- `operator` → create & manage jobs
- `viewer` → read-only access

---

## 🔄 Job Lifecycle

1. Job created via API
2. Stored in PostgreSQL
3. Published to Redis queue
4. Processed by Celery worker
5. Event emitted to Kafka
6. Consumer processes event (audit, logging, etc.)

---

## 🔒 Advanced Concepts Implemented

- Idempotency
- Distributed Locking
- Dead Letter Queue
- Retry Mechanisms
- Event-Driven Architecture
- Outbox Pattern
- Duplicate Event Protection
- JWT Authentication
- Refresh Token Rotation
- Token Reuse Detection
- Role-Based Access Control (RBAC)

---

## 📦 API Endpoints (Examples)

### 🔐 Auth
- `POST /auth/login` → Login (returns access + refresh token)
- `POST /auth/refresh` → Get new tokens
- `POST /auth/logout` → Logout (revoke token)
- `GET /auth/me` → Current user

### 📌 Jobs
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

This project simulates real-world backend systems used in companies like:

Uber
Netflix
Amazon

and focuses on:

Scalability
Fault tolerance
Distributed systems design
Secure authentication & session management
🧭 Roadmap
Multi-tenant architecture (organization-based isolation)
Rate limiting & quotas
Advanced monitoring (Grafana dashboards)
Horizontal scaling improvements
👤 Author

Atakan Avsever

GitHub: https://github.com/Atakan-Avs
LinkedIn: https://linkedin.com/in/atakanavsever