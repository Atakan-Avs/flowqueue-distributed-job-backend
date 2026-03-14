# FlowQueue — Distributed Job Processing Backend

FlowQueue is a **production-style distributed job processing backend** built with FastAPI, Celery, and Redis.

The system allows clients to submit jobs through an API and process them asynchronously using worker processes.  
It includes reliability mechanisms such as retries, dead-letter queues, distributed locks, and observability tools.

This project demonstrates **real-world backend architecture patterns** used in scalable systems.

---

# Architecture Overview

FlowQueue uses a distributed architecture composed of multiple services:

Client → FastAPI API → Redis Queue → Celery Workers → PostgreSQL  
                                      ↓  
                                Prometheus Metrics  
                                      ↓  
                                  Grafana

Components:

- **FastAPI** handles API requests
- **Redis** acts as the message broker
- **Celery workers** process background jobs
- **PostgreSQL** stores job metadata
- **Prometheus** collects metrics
- **Grafana** visualizes system behavior

---

# Features

### Asynchronous Job Processing
Jobs are submitted through the API and processed asynchronously using Celery workers.

### Priority Queues
Jobs can be assigned different priorities:

- `high`
- `normal`
- `low`

Workers process higher priority jobs first.

### Idempotency Protection
The API supports an `Idempotency-Key` header to prevent duplicate job submissions.

### Retry Mechanism
Failed jobs are retried automatically with exponential backoff.

### Dead Letter Queue (DLQ)
Jobs that exceed the retry limit are moved to a **Dead Letter Queue**.

This prevents infinite retry loops and allows operators to inspect failed tasks.

### Distributed Locking
A Redis-based distributed lock ensures that **a job cannot be processed by multiple workers simultaneously**.

### Structured Logging
The system produces structured logs with request IDs for traceability.

### Rate Limiting
API endpoints are protected using Redis-based rate limiting.

### Observability & Monitoring

FlowQueue exposes Prometheus metrics such as:

- total jobs created
- completed jobs
- failed jobs
- retry counts
- dead letter jobs

These metrics are visualized in **Grafana dashboards**.

---

# Tech Stack

Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic

Distributed Processing

- Celery
- Redis

Observability

- Prometheus
- Grafana

Infrastructure

- Docker
- Docker Compose

---

# Project Structure


flowqueue
├── app
│
├── api
│ └── v1
│ └── endpoints
│ └── jobs.py
│
├── core
│ ├── config.py
│ ├── celery_app.py
│ ├── distributed_lock.py
│ ├── metrics.py
│ ├── logging.py
│
├── db
│ └── session.py
│
├── repositories
│ └── job_repository.py
│
├── services
│ └── job_service.py
│
├── tasks
│ └── job_tasks.py
│
└── utils
└── enums.py


---

# Running the Project

Clone the repository


git clone https://github.com/YOUR_USERNAME/flowqueue-distributed-job-backend.git

cd flowqueue-distributed-job-backend


Start all services


docker compose up --build


Services

| Service | URL |
|------|------|
API | http://localhost:8000 |
Flower (Celery UI) | http://localhost:5555 |
Prometheus | http://localhost:9090 |
Grafana | http://localhost:3000 |

---

# API Endpoints

Create Job


POST /api/v1/jobs


Example request


{
"job_type": "report",
"payload": "generate monthly report",
"priority": "normal"
}


Get Job


GET /api/v1/jobs/{job_id}


Retry Job


POST /api/v1/jobs/{job_id}/retry


List Jobs


GET /api/v1/jobs


Dead Letter Jobs


GET /api/v1/jobs/dead-letter


Requeue Dead Letter Job


POST /api/v1/jobs/{job_id}/requeue


---

# Monitoring

Prometheus metrics endpoint


GET /metrics


Metrics include


flowqueue_jobs_created_total
flowqueue_jobs_completed_total
flowqueue_jobs_failed_total
flowqueue_jobs_dead_letter_total
flowqueue_job_retries_total


Grafana dashboards visualize system activity in real time.

---

# Example Job Lifecycle

1️⃣ Client sends a job request  
2️⃣ API stores job in PostgreSQL  
3️⃣ Job is pushed to Redis queue  
4️⃣ Celery worker processes the job  
5️⃣ Job succeeds or fails  
6️⃣ Failed jobs are retried  
7️⃣ Jobs exceeding retry limit move to DLQ

---

# Future Improvements

Potential improvements for production systems:

- Horizontal worker autoscaling
- Authentication & RBAC
- Job scheduling (Celery Beat)
- Kubernetes deployment
- Alerting system
- Distributed tracing (OpenTelemetry)

---

# Author

**Atakan Avsever**

Backend Developer focused on distributed systems, API design, and scalable backend architectures.

GitHub:  
https://github.com/Atakan-Avs