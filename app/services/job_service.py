from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.job_repository import JobRepository
from app.db.models.job import Job
from app.utils.enums import JobStatus


class JobService:
    @staticmethod
    def create_job(db: Session, job_type: str, payload: str):
        job = Job(
            job_type=job_type,
            payload=payload,
            status=JobStatus.PENDING.value,
        )
        return JobRepository.create(db, job)

    @staticmethod
    def get_job(db: Session, job_id: UUID):
        return JobRepository.get_by_id(db, job_id)

    @staticmethod
    def list_jobs(
        db: Session,
        skip: int = 0,
        limit: int = 10,
        status: str | None = None,
    ):
        return JobRepository.get_all(
            db=db,
            skip=skip,
            limit=limit,
            status=status,
        )

    @staticmethod
    def retry_job(db: Session, job_id: UUID):
        job = JobRepository.get_by_id(db, job_id)

        if not job:
            return None, "not_found"

        if job.status == JobStatus.PROCESSING.value:
            return None, "processing"

        job.status = JobStatus.PENDING.value
        job.result = None
        job.error_message = None
        job.retry_count += 1

        updated_job = JobRepository.update(db, job)
        return updated_job, None