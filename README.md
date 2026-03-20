# FlowQueue – Distributed Job Processing Backend 

FlowQueue is a production-style distributed job processing backend built to explore how scalable background processing systems work.

The project demonstrates a queue-based architecture where jobs are created through an API, placed into Redis queues, and processed asynchronously by Celery workers.

It also includes observability tools such as Prometheus and Grafana to monitor system behavior.

---

# Architecture

The system follows a distributed worker architecture:

Client  
↓  
FastAPI API  
↓  
Redis Queue  
↓  
Celery Workers  
↓  
PostgreSQL Database  

Jobs are created through the API and placed into Redis queues. Workers consume jobs from these queues and update their status in the database.

---

# Key Features

### Job Management API

Built with FastAPI, the API allows clients to:

• Create jobs  
• List jobs  
• Retrieve job status  
• Retry failed jobs  
• Requeue dead letter jobs  

Example endpoints:


POST /api/v1/jobs
GET /api/v1/jobs
GET /api/v1/jobs/{job_id}
POST /api/v1/jobs/{job_id}/retry
POST /api/v1/jobs/{job_id}/requeue
GET /api/v1/jobs/dead-letter


---

# Distributed Queue System

The project uses **Redis + Celery** for asynchronous job processing.

Jobs are pushed to Redis queues and consumed by Celery workers.

Multiple workers can run simultaneously, allowing horizontal scaling.

---

# Priority Queue Support

Jobs support priority levels:


high
normal
low


Workers listen to multiple queues so higher priority jobs are processed first.

---

# Retry Mechanism

Failed jobs are automatically retried.

Retry behavior:


MAX_RETRY = 3


If a job fails multiple times it will eventually be moved to the Dead Letter Queue.

---

# Dead Letter Queue (DLQ)

If a job fails after reaching the retry limit, it is marked as:


is_dead_letter = true


Dead letter jobs can later be inspected or requeued.

This pattern is commonly used in production systems to prevent infinite retry loops.

---

# Idempotency Protection

The API supports an **Idempotency-Key header**.

This prevents duplicate job creation when the same request is sent multiple times.

Example:


Idempotency-Key: 12345-abc


If the request is repeated, the same job is returned instead of creating a new one.

---

# Distributed Locking

The system uses Redis-based distributed locks to ensure that a job cannot be processed simultaneously by multiple workers.

Lock format:


lock:job:{job_id}


This protects the system from concurrency issues in distributed environments.

---

# Rate Limiting

Basic rate limiting is implemented using Redis to prevent API abuse or excessive request bursts.

---

# Observability

Monitoring and observability are built into the system.

### Structured Logging

Logs include useful context fields such as:


request_id
job_id
status
retry_count


---

### Prometheus Metrics

The API exposes metrics such as:


flowqueue_jobs_created_total
flowqueue_jobs_completed_total
flowqueue_jobs_failed_total
flowqueue_jobs_dead_letter_total
flowqueue_job_retries_total


---

### Grafana Dashboard

Metrics can be visualized using Grafana dashboards to monitor:

• jobs created  
• jobs completed  
• job failures  
• dead letter jobs  
• retries  

---

### Flower Monitoring

Celery workers can be monitored in real time using Flower.


http://localhost:5555


---

# Testing

The project includes automated tests using **pytest**.

Current test coverage includes:

• API endpoint tests  
• Job service logic tests  
• Distributed lock behavior tests  

Run tests with:


pytest


---

# Tech Stack

Backend


Python
FastAPI
SQLAlchemy


Queue & Workers


Redis
Celery


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


---

# Running the Project

Clone the repository


git clone https://github.com/Atakan-Avs/flowqueue-distributed-job-backend


Navigate to the project


cd flowqueue-distributed-job-backend


Start the system


docker compose up --build


Services will start:

• FastAPI API  
• Redis  
• PostgreSQL  
• Celery workers  
• Celery beat scheduler  
• Prometheus  
• Grafana  
• Flower monitoring  

---

# Learning Goals

This project was built to better understand:

• distributed background job processing  
• queue based system design  
• worker architectures  
• retry and dead letter patterns  
• distributed locking  
• observability and monitoring  

---

# Future Improvements

Potential improvements for the project include:

• job timeout handling  
• job cancellation support  
• distributed tracing (OpenTelemetry)  
• advanced rate limiting strategies  

---

# Author

Atakan Avsever

GitHub  
https://github.com/Atakan-Avs
