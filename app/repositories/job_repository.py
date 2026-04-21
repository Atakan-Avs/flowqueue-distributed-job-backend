from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.job import Job
from app.utils.enums import JobStatus


class JobRepository:
    @staticmethod
    def create(db: Session, job: Job):
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_by_id(db: Session, job_id: UUID, organization_id):
        return db.query(Job).filter(
            Job.id == job_id,
            Job.organization_id == organization_id,
        ).first()
        
    @staticmethod
    def get_by_id_unscoped(db: Session, job_id: UUID):
        return db.query(Job).filter(Job.id == job_id).first()

    @staticmethod
    def get_by_idempotency_key(db: Session, idempotency_key: str):
        return db.query(Job).filter(Job.idempotency_key == idempotency_key).first()

    @staticmethod
    def get_all(
        db: Session,
        organization_id,
        skip: int = 0,
        limit: int = 10,
        status: str | None = None,
    ):
        query = db.query(Job).filter(Job.organization_id == organization_id)

        if status:
            query = query.filter(Job.status == status)

        items = (
            query.order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        total_query = db.query(func.count(Job.id)).filter(
            Job.organization_id == organization_id
        )

        if status:
            total_query = total_query.filter(Job.status == status)

        total = total_query.scalar() or 0

        return items, total

    @staticmethod
    def update(db: Session, job: Job):
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_metrics(db: Session, organization_id):
        total_jobs = db.query(func.count(Job.id)).filter(
            Job.organization_id == organization_id
        ).scalar() or 0

        pending = db.query(func.count(Job.id)).filter(
            Job.organization_id == organization_id,
            Job.status == JobStatus.PENDING.value
        ).scalar() or 0

        processing = db.query(func.count(Job.id)).filter(
            Job.organization_id == organization_id,
            Job.status == JobStatus.PROCESSING.value
        ).scalar() or 0

        completed = db.query(func.count(Job.id)).filter(
            Job.organization_id == organization_id,
            Job.status == JobStatus.COMPLETED.value
        ).scalar() or 0

        failed = db.query(func.count(Job.id)).filter(
            Job.organization_id == organization_id,
            Job.status == JobStatus.FAILED.value
        ).scalar() or 0

        return dict(
            total_jobs=total_jobs,
            pending=pending,
            processing=processing,
            completed=completed,
            failed=failed,
        )

    @staticmethod
    def get_dead_letter_jobs(
        db: Session,
        organization_id,
        skip: int = 0,
        limit: int = 10,
    ):
        query = db.query(Job).filter(
            Job.organization_id == organization_id,
            Job.is_dead_letter.is_(True)
        )

        items = (
            query.order_by(Job.dead_lettered_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        total = db.query(func.count(Job.id)).filter(
            Job.organization_id == organization_id,
            Job.is_dead_letter.is_(True)
        ).scalar() or 0

        return items, total