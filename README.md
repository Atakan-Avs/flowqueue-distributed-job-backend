# FlowQueue – Distributed Job Processing Backend

FlowQueue is a production-oriented backend service designed to handle **asynchronous job processing** using modern backend technologies such as FastAPI, Celery, Redis, and PostgreSQL.

The system allows clients to create background jobs which are processed by worker services while tracking job status and results.

This project demonstrates how to design a scalable backend system with a **task queue architecture** commonly used in real production environments.

---

# Features

- Asynchronous job processing
- Background worker system using Celery
- Redis message broker
- PostgreSQL persistent job storage
- Job lifecycle tracking
- Retry mechanism for failed jobs
- Pagination and filtering
- Dockerized environment
- Database migrations using Alembic
- Clean layered backend architecture

---

# Tech Stack

Backend Framework
- FastAPI

Task Queue
- Celery

Message Broker
- Redis

Database
- PostgreSQL

ORM
- SQLAlchemy

Migrations
- Alembic

Containerization
- Docker
- Docker Compose

Language
- Python

---

# Architecture Overview

The system follows a typical **asynchronous processing architecture**.


Client Request
│
▼
FastAPI API
│
▼
PostgreSQL (store job)
│
▼
Redis Queue
│
▼
Celery Worker
│
▼
Process Job
│
▼
Update Job Status


Job statuses:


pending
processing
completed
failed


---

# Project Structure


flowqueue/
│
├── app/
│ ├── api/
│ │ └── v1/
│ │ └── endpoints/
│ │ └── jobs.py
│ │
│ ├── core/
│ │ ├── config.py
│ │ └── celery_app.py
│ │
│ ├── db/
│ │ ├── session.py
│ │ └── models/
│ │ └── job.py
│ │
│ ├── repositories/
│ │ └── job_repository.py
│ │
│ ├── services/
│ │ └── job_service.py
│ │
│ ├── tasks/
│ │ └── job_tasks.py
│ │
│ ├── schemas/
│ │ └── job.py
│ │
│ └── main.py
│
├── migrations/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md


---

# API Endpoints

Create Job


POST /api/v1/jobs


Example request:

```json
{
  "job_type": "report",
  "payload": "generate monthly report"
}

Get Job

GET /api/v1/jobs/{job_id}

List Jobs

GET /api/v1/jobs

Pagination example:

/api/v1/jobs?skip=0&limit=10

Filtering example:

/api/v1/jobs?status=completed

Retry Failed Job

POST /api/v1/jobs/{job_id}/retry
Example Job Lifecycle

Create Job

POST /api/v1/jobs

Initial state:

pending

Worker processing:

processing

Finished:

completed

If an error occurs:

failed

Failed jobs can be retried using the retry endpoint.

Running the Project

Clone the repository

git clone https://github.com/YOUR_USERNAME/flowqueue-distributed-job-backend.git
cd flowqueue-distributed-job-backend

Start the system using Docker:

docker compose up --build

The following services will start:

FastAPI API server

PostgreSQL database

Redis message broker

Celery worker

Access API

API Documentation (Swagger)

http://localhost:8000/docs
Development Concepts Demonstrated

This project demonstrates several backend engineering concepts:

asynchronous task processing

queue-based architecture

retry strategies

service layer architecture

repository pattern

Dockerized micro-service style backend

database migration workflows

background workers

Possible Future Improvements

Rate limiting

Idempotency keys

Structured logging

Request tracing

Prometheus monitoring

Admin dashboard

Job scheduling

Dead letter queues

Author

Backend project developed as part of a portfolio demonstrating backend engineering concepts using Python and modern infrastructure tooling.


