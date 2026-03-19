import logging
import time
from datetime import datetime
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
from app.utils.enums import JobStatus


logger = logging.getLogger(__name__)

MAX_RETRY_COUNT = 3


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

    try:
        job = JobRepository.get_by_id(db, UUID(job_id))

        if not job:
            logger.warning("Job not found in worker | job_id=%s", job_id)
            return

        if job.is_dead_letter:
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

        time.sleep(5)

        if "fail" in job.payload.lower():
            raise ValueError("Simulated job failure triggered by payload.")

        result = f"processed payload: {job.payload}"

        job.status = JobStatus.COMPLETED.value
        job.result = result
        job.error_message = None
        JobRepository.update(db, job)
        
        jobs_completed_total.inc()

        logger.info(
            "Job completed successfully | job_id=%s | status=%s",
            job.id,
            job.status,
        )

    except Exception as exc:
        job = JobRepository.get_by_id(db, UUID(job_id))

        if job:
            job.retry_count += 1
            job_retries_total.inc()
            jobs_failed_total.inc()

            if job.retry_count >= MAX_RETRY_COUNT:
                job.status = JobStatus.FAILED.value
                job.error_message = str(exc)
                job.is_dead_letter = True
                job.dead_lettered_at = datetime.utcnow()
                JobRepository.update(db, job)
                
                jobs_dead_letter_total.inc()

                logger.error(
                    "Job moved to dead letter queue | job_id=%s | error=%s | retry_count=%s",
                    job.id,
                    str(exc),
                    job.retry_count,
                )
                return

            job.status = JobStatus.FAILED.value
            job.error_message = str(exc)
            JobRepository.update(db, job)

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