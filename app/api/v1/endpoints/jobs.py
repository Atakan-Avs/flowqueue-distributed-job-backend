import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limiter
from app.db.session import get_db
from app.schemas.job import JobCreate, JobListResponse, JobResponse
from app.schemas.metrics import JobMetricsResponse
from app.services.job_service import JobService
from app.tasks.job_tasks import process_job
from app.utils.enums import JobPriority, JobStatus

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/jobs", response_model=JobResponse, status_code=201)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limiter),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    valid_priorities = {item.value for item in JobPriority}
    if job_data.priority not in valid_priorities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority. Allowed values: {', '.join(valid_priorities)}",
        )

    job, created = JobService.create_job(
        db=db,
        job_type=job_data.job_type,
        payload=job_data.payload,
        priority=job_data.priority,
        idempotency_key=idempotency_key,
    )

    if created:
        logger.info(
            "Job created and queued | job_id=%s | job_type=%s | status=%s | priority=%s | idempotency_key=%s",
            job.id,
            job.job_type,
            job.status,
            job.priority,
            job.idempotency_key,
        )
        process_job.apply_async(args=[str(job.id)], queue=job.priority)
    else:
        logger.info(
            "Duplicate job prevented by idempotency key | job_id=%s | idempotency_key=%s",
            job.id,
            job.idempotency_key,
        )

    return job


@router.get("/jobs", response_model=JobListResponse)
def list_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limiter),
):
    if status is not None:
        valid_statuses = {item.value for item in JobStatus}
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Allowed values: {', '.join(valid_statuses)}",
            )

    items, total = JobService.list_jobs(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
    )

    logger.info(
        "Jobs listed | total=%s | skip=%s | limit=%s | status_filter=%s",
        total,
        skip,
        limit,
        status,
    )

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/jobs/dead-letter", response_model=JobListResponse)
def list_dead_letter_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: None = Depends(rate_limiter),
):
    items, total = JobService.list_dead_letter_jobs(
        db=db,
        skip=skip,
        limit=limit,
    )

    logger.info(
        "Dead letter jobs listed | total=%s | skip=%s | limit=%s",
        total,
        skip,
        limit,
    )

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit,
    }


@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limiter),
):
    job = JobService.get_job(db, job_id)

    if not job:
        logger.warning("Job not found | job_id=%s", job_id)
        raise HTTPException(status_code=404, detail="Job not found")

    logger.info(
        "Job retrieved | job_id=%s | status=%s | retry_count=%s",
        job.id,
        job.status,
        job.retry_count,
    )

    return job


@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
def retry_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limiter),
):
    job, error = JobService.retry_job(db, job_id)

    if error == "not_found":
        logger.warning("Retry failed - job not found | job_id=%s", job_id)
        raise HTTPException(status_code=404, detail="Job not found")

    if error == "processing":
        logger.warning("Retry rejected - job still processing | job_id=%s", job_id)
        raise HTTPException(
            status_code=400,
            detail="Processing jobs cannot be retried",
        )

    logger.info(
        "Job retry triggered and queued | job_id=%s | retry_count=%s",
        job.id,
        job.retry_count,
    )

    process_job.apply_async(args=[str(job.id)], queue=job.priority)
    return job


@router.post("/jobs/{job_id}/requeue", response_model=JobResponse)
def requeue_dead_letter_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limiter),
):
    job, error = JobService.requeue_dead_letter_job(db, job_id)

    if error == "not_found":
        logger.warning("Requeue failed - job not found | job_id=%s", job_id)
        raise HTTPException(status_code=404, detail="Job not found")

    if error == "not_dead_letter":
        logger.warning("Requeue rejected - job is not in dead letter queue | job_id=%s", job_id)
        raise HTTPException(status_code=400, detail="Job is not in dead letter queue")

    logger.info(
        "Dead letter job requeued | job_id=%s | priority=%s",
        job.id,
        job.priority,
    )

    process_job.apply_async(args=[str(job.id)], queue=job.priority)
    return job


@router.get("/metrics/jobs", response_model=JobMetricsResponse)
def job_metrics(
    db: Session = Depends(get_db),
    _: None = Depends(rate_limiter),
):
    metrics = JobService.get_metrics(db)

    logger.info(
        "Job metrics retrieved | total_jobs=%s | pending=%s | processing=%s | completed=%s | failed=%s",
        metrics["total_jobs"],
        metrics["pending"],
        metrics["processing"],
        metrics["completed"],
        metrics["failed"],
    )

    return metrics