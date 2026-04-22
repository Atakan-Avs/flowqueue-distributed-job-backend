import json
import logging
from datetime import datetime, timezone

from app.core.celery_app import celery_app
from app.core.kafka_producer import publish_job_event
from app.core.metrics import jobs_created_total, jobs_dead_letter_total
from app.db.session import SessionLocal
from app.repositories.job_repository import JobRepository
from app.repositories.outbox_repository import OutboxRepository
from app.tasks.job_tasks import process_job
from app.tasks.scheduled_tasks import create_scheduled_job
from app.utils.enums import JobStatus

logger = logging.getLogger(__name__)

STUCK_JOB_TIMEOUT_MINUTES = 10
MAX_RETRY_COUNT = 3


@celery_app.task(name="app.tasks.beat_tasks.enqueue_scheduled_report")
def enqueue_scheduled_report():
    job_id = create_scheduled_job()
    jobs_created_total.inc()

    logger.info(
        "Scheduled job created by Celery Beat | job_id=%s | job_type=%s",
        job_id,
        "scheduled_report",
    )

    process_job.apply_async(args=[job_id], queue="normal")


@celery_app.task(name="app.tasks.beat_tasks.recover_stuck_jobs")
def recover_stuck_jobs():
    db = SessionLocal()

    try:
        stuck_jobs = JobRepository.get_stuck_jobs(
            db,
            timeout_minutes=STUCK_JOB_TIMEOUT_MINUTES,
        )

        if not stuck_jobs:
            logger.info("No stuck jobs found")
            return

        for job in stuck_jobs:
            job.retry_count += 1

            if job.retry_count >= MAX_RETRY_COUNT:
                job.status = JobStatus.FAILED.value
                job.error_message = (
                    "Job moved to dead letter after being stuck in processing state."
                )
                job.is_dead_letter = True
                job.dead_lettered_at = datetime.now(timezone.utc)
                JobRepository.update(db, job)

                jobs_dead_letter_total.inc()

                logger.error(
                    "Stuck job moved to dead letter | job_id=%s | retry_count=%s",
                    job.id,
                    job.retry_count,
                )
                continue

            job.status = JobStatus.PENDING.value
            job.error_message = "Recovered from stuck processing state."
            JobRepository.update(db, job)

            process_job.delay(str(job.id))

            logger.warning(
                "Recovered stuck job and requeued | job_id=%s | retry_count=%s",
                job.id,
                job.retry_count,
            )

    finally:
        db.close()


@celery_app.task(name="app.tasks.beat_tasks.publish_outbox_events")
def publish_outbox_events():
    db = SessionLocal()

    try:
        unpublished_events = OutboxRepository.get_unpublished_events(db, limit=100)

        if not unpublished_events:
            logger.info("No unpublished outbox events found")
            return

        for event in unpublished_events:
            payload = json.loads(event.payload)

            publish_job_event(payload)
            OutboxRepository.mark_as_published(db, event)

            logger.info(
                "Outbox event published to Kafka | event_id=%s | event_type=%s",
                event.id,
                event.event_type,
            )

    finally:
        db.close()