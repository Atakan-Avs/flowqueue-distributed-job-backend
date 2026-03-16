from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.job import Job
from app.repositories.job_repository import JobRepository
from app.utils.enums import JobPriority, JobStatus


class JobService:
    @staticmethod
    def create_job(
        db: Session,
        job_type: str,
        payload: str,
        priority: str = JobPriority.NORMAL.value,
        idempotency_key: str | None = None,
    ):
        if idempotency_key:
            existing_job = JobRepository.get_by_idempotency_key(db, idempotency_key)
            if existing_job:
                return existing_job, False

        job = Job(
            job_type=job_type,
            payload=payload,
            status=JobStatus.PENDING.value,
            priority=priority,
            idempotency_key=idempotency_key,
        )

        try:
            created_job = JobRepository.create(db, job)
            return created_job, True
        except IntegrityError:
            db.rollback()

            if not idempotency_key:
                raise

            existing_job = JobRepository.get_by_idempotency_key(db, idempotency_key)
            if existing_job:
                return existing_job, False

            raise

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

        if getattr(job, "is_dead_letter", False):
            return None, "dead_letter"

        if job.status == JobStatus.PROCESSING.value:
            return None, "processing"

        if job.status == JobStatus.COMPLETED.value:
            return None, "completed"

        if job.status != JobStatus.FAILED.value:
            return None, "invalid_status"

        job.status = JobStatus.PENDING.value
        job.result = None
        job.error_message = None
        job.retry_count += 1

        updated_job = JobRepository.update(db, job)
        return updated_job, None

    @staticmethod
    def list_dead_letter_jobs(
        db: Session,
        skip: int = 0,
        limit: int = 10,
    ):
        return JobRepository.get_dead_letter_jobs(
            db=db,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    def requeue_dead_letter_job(db: Session, job_id: UUID):
        job = JobRepository.get_by_id(db, job_id)

        if not job:
            return None, "not_found"

        if not job.is_dead_letter:
            return None, "not_dead_letter"

        job.status = JobStatus.PENDING.value
        job.result = None
        job.error_message = None
        job.is_dead_letter = False
        job.dead_lettered_at = None

        updated_job = JobRepository.update(db, job)
        return updated_job, None

    @staticmethod
    def get_metrics(db: Session):
        return JobRepository.get_metrics(db)