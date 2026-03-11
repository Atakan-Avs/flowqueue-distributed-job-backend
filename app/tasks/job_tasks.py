import time
from uuid import UUID

from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.repositories.job_repository import JobRepository
from app.utils.enums import JobStatus


@celery_app.task(name="app.tasks.job_tasks.process_job", bind=True, max_retries=3)
def process_job(self, job_id: str):
    db = SessionLocal()

    try:
        job = JobRepository.get_by_id(db, UUID(job_id))

        if not job:
            return

        job.status = JobStatus.PROCESSING.value
        JobRepository.update(db, job)

        time.sleep(5)

        # demo hata testi için:
        # payload içinde "fail" geçerse hata üretelim
        if "fail" in job.payload.lower():
            raise ValueError("Simulated job failure triggered by payload.")

        result = f"processed payload: {job.payload}"

        job.status = JobStatus.COMPLETED.value
        job.result = result
        job.error_message = None
        JobRepository.update(db, job)

    except Exception as exc:
        job = JobRepository.get_by_id(db, UUID(job_id))

        if job:
            job.status = JobStatus.FAILED.value
            job.error_message = str(exc)
            JobRepository.update(db, job)

        raise self.retry(exc=exc, countdown=5)

    finally:
        db.close()