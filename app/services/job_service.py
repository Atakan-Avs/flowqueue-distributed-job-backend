from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models.job import Job
from app.db.models.job_attempt import JobAttempt
from app.handlers.factory import JobHandlerFactory
from app.repositories.job_repository import JobRepository
from app.repositories.outbox_repository import OutboxRepository
from app.utils.enums import JobStatus


class JobService:
    @staticmethod
    def create_job(
        db: Session,
        job_type: str,
        payload: str,
        priority: str,
        organization_id,
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
            organization_id=organization_id,
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
    def get_job(db: Session, job_id: UUID, organization_id):
        return JobRepository.get_by_id(db, job_id, organization_id)

    @staticmethod
    def list_jobs(
        db: Session,
        organization_id,
        skip: int = 0,
        limit: int = 10,
        status: str | None = None,
    ):
        return JobRepository.get_all(
            db=db,
            organization_id=organization_id,
            skip=skip,
            limit=limit,
            status=status,
        )

    @staticmethod
    def retry_job(db: Session, job_id: UUID, organization_id):
        job = JobRepository.get_by_id(db, job_id, organization_id)

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
        organization_id,
        skip: int = 0,
        limit: int = 10,
    ):
        return JobRepository.get_dead_letter_jobs(
            db=db,
            organization_id=organization_id,
            skip=skip,
            limit=limit,
        )

    @staticmethod
    def requeue_dead_letter_job(db: Session, job_id: UUID, organization_id):
        job = JobRepository.get_by_id(db, job_id, organization_id)

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
    def get_metrics(db: Session, organization_id):
        return JobRepository.get_metrics(db, organization_id)

    @staticmethod
    def execute_job_logic(job: Job):
        handler = JobHandlerFactory.get_handler(job.job_type)
        result = handler.handle(job.payload)

        job.status = JobStatus.COMPLETED.value
        job.result = result
        job.error_message = None
        return job

    @staticmethod
    def start_attempt(db: Session, job: Job):
        attempt = JobAttempt(
            job_id=job.id,
            attempt_number=job.retry_count + 1,
            status="processing",
            started_at=datetime.utcnow(),
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt

    @staticmethod
    def mark_attempt_success(db: Session, attempt: JobAttempt):
        attempt.status = "success"
        attempt.finished_at = datetime.utcnow()
        db.add(attempt)
        db.commit()

    @staticmethod
    def mark_attempt_failed(db: Session, attempt: JobAttempt, error_message: str):
        attempt.status = "failed"
        attempt.error_message = error_message
        attempt.finished_at = datetime.utcnow()
        db.add(attempt)
        db.commit()

    @staticmethod
    def handle_job_failure(
        db: Session,
        job: Job,
        error_message: str,
        max_retry_count: int,
    ):
        job.retry_count += 1
        job.status = JobStatus.FAILED.value
        job.error_message = error_message

        moved_to_dead_letter = False

        if job.retry_count >= max_retry_count:
            job.is_dead_letter = True
            job.dead_lettered_at = datetime.utcnow()
            moved_to_dead_letter = True

        JobRepository.update(db, job)
        return job, moved_to_dead_letter

    @staticmethod
    def publish_job_completed_event(db: Session, job: Job):
        OutboxRepository.create_event(
            db=db,
            event_type="job.completed",
            aggregate_id=job.id,
            payload={
                "event_id": str(uuid4()),
                "event_type": "job.completed",
                "job_id": str(job.id),
                "job_type": job.job_type,
                "status": job.status,
                "priority": job.priority,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def publish_job_failed_event(db: Session, job: Job, error_message: str):
        OutboxRepository.create_event(
            db=db,
            event_type="job.failed",
            aggregate_id=job.id,
            payload={
                "event_id": str(uuid4()),
                "event_type": "job.failed",
                "job_id": str(job.id),
                "job_type": job.job_type,
                "status": job.status,
                "priority": job.priority,
                "retry_count": job.retry_count,
                "error_message": error_message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def publish_job_dead_letter_event(db: Session, job: Job, error_message: str):
        OutboxRepository.create_event(
            db=db,
            event_type="job.dead_lettered",
            aggregate_id=job.id,
            payload={
                "event_id": str(uuid4()),
                "event_type": "job.dead_lettered",
                "job_id": str(job.id),
                "job_type": job.job_type,
                "status": job.status,
                "priority": job.priority,
                "retry_count": job.retry_count,
                "error_message": error_message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )