from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.job import Job


class JobRepository:
    @staticmethod
    def create(db: Session, job: Job):
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_by_id(db: Session, job_id: UUID):
        return db.query(Job).filter(Job.id == job_id).first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 10,
        status: str | None = None,
    ):
        query = db.query(Job)

        if status:
            query = query.filter(Job.status == status)

        items = (
            query.order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

        total_query = db.query(func.count(Job.id))
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