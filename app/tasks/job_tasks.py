import logging
import time
from uuid import UUID

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.repositories.job_repository import JobRepository
from app.utils.enums import JobStatus

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.job_tasks.process_job", bind=True, max_retries=3)
def process_job(self, job_id: str):
    db = SessionLocal()

    try:
        job = JobRepository.get_by_id(db, UUID(job_id))

        if not job:
            logger.warning("Job not found in worker | job_id=%s", job_id)
            return

        job.status = JobStatus.PROCESSING.value
        JobRepository.update(db, job)

        logger.info(
            "Job processing started | job_id=%s | job_type=%s",
            job.id,
            job.job_type,
        )

        time.sleep(5)

        if "fail" in job.payload.lower():
            raise ValueError("Simulated job failure triggered by payload.")

        result = f"processed payload: {job.payload}"

        job.status = JobStatus.COMPLETED.value
        job.result = result
        job.error_message = None
        JobRepository.update(db, job)

        logger.info(
            "Job completed successfully | job_id=%s | status=%s",
            job.id,
            job.status,
        )

    except Exception as exc:
        job = JobRepository.get_by_id(db, UUID(job_id))

        if job:
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
        db.close()