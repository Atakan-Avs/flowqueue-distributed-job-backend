import logging
from uuid import UUID

from app.core.celery_app import celery_app
from app.core.distributed_lock import RedisLock
from app.core.metrics import (
    job_retries_total,
    jobs_completed_total,
    jobs_dead_letter_total,
    jobs_failed_total,
)
from app.db.session import SessionLocal
from app.repositories.job_repository import JobRepository
from app.services.job_service import JobService
from app.utils.enums import JobStatus

logger = logging.getLogger(__name__)

MAX_RETRY_COUNT = 3
HIGH_FAILURE_RETRY_THRESHOLD = 2


@celery_app.task(name="app.tasks.job_tasks.process_job", bind=True, max_retries=3)
def process_job(self, job_id: str):
    db = SessionLocal()
    lock = RedisLock(key=f"lock:job:{job_id}", timeout=60)

    if not lock.acquire():
        logger.warning(
            "Job skipped because lock is already held | job_id=%s",
            job_id,
        )
        db.close()
        return

    attempt = None

    try:
        job = JobRepository.get_by_id_unscoped(db, UUID(job_id))

        if not job:
            logger.warning("Job not found in worker | job_id=%s", job_id)
            return

        attempt = JobService.start_attempt(db, job)

        if job.is_dead_letter:
            if attempt:
                JobService.mark_attempt_failed(
                    db,
                    attempt,
                    "Dead letter job cannot be processed directly.",
                )

            logger.warning(
                "Dead letter job cannot be processed directly | job_id=%s",
                job.id,
            )
            return

        job.status = JobStatus.PROCESSING.value
        JobRepository.update(db, job)

        logger.info(
            "Job processing started | job_id=%s | job_type=%s | priority=%s",
            job.id,
            job.job_type,
            job.priority,
        )

        job = JobService.execute_job_logic(job)
        JobRepository.update(db, job)

        if attempt:
            JobService.mark_attempt_success(db, attempt)

        JobService.publish_job_completed_event(db, job)
        jobs_completed_total.inc()

        logger.info(
            "Job completed successfully | job_id=%s | status=%s",
            job.id,
            job.status,
        )

    except Exception as exc:
        job = JobRepository.get_by_id_unscoped(db, UUID(job_id))

        if attempt:
            JobService.mark_attempt_failed(db, attempt, str(exc))

        if job:
            job, moved_to_dead_letter = JobService.handle_job_failure(
                db=db,
                job=job,
                error_message=str(exc),
                max_retry_count=MAX_RETRY_COUNT,
            )

            jobs_failed_total.inc()

            if job.retry_count >= HIGH_FAILURE_RETRY_THRESHOLD:
                logger.warning(
                    "High failure risk detected | job_id=%s | job_type=%s | retry_count=%s | error=%s",
                    job.id,
                    job.job_type,
                    job.retry_count,
                    str(exc),
                )

            if moved_to_dead_letter:
                JobService.publish_job_dead_letter_event(db, job, str(exc))
                jobs_dead_letter_total.inc()

                logger.error(
                    "Job moved to dead letter queue | job_id=%s | error=%s | retry_count=%s",
                    job.id,
                    str(exc),
                    job.retry_count,
                )
                return

            job_retries_total.inc()
            JobService.publish_job_failed_event(db, job, str(exc))

            logger.error(
                "Job processing failed | job_id=%s | error=%s | retry_count=%s",
                job.id,
                str(exc),
                job.retry_count,
            )

        raise self.retry(exc=exc, countdown=5)

    finally:
        if lock.acquired:
            lock.release()
        db.close()