from app.db.models.job import Job
from app.db.session import SessionLocal
from app.utils.enums import JobPriority, JobStatus


def create_scheduled_job():
    db = SessionLocal()
    try:
        job = Job(
            job_type="scheduled_report",
            payload="daily scheduled report job",
            status=JobStatus.PENDING.value,
            priority=JobPriority.NORMAL.value,
            idempotency_key=None,
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return str(job.id)
    finally:
        db.close()