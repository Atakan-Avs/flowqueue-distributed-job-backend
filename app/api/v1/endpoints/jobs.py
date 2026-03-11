import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.rate_limit import rate_limiter
from app.db.session import get_db
from app.schemas.job import JobCreate, JobListResponse, JobResponse
from app.services.job_service import JobService
from app.tasks.job_tasks import process_job
from app.utils.enums import JobStatus

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/jobs", response_model=JobResponse, status_code=201)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limiter),
):
    job = JobService.create_job(
        db,
        job_type=job_data.job_type,
        payload=job_data.payload,
    )

    logger.info(
        "Job created and queued | job_id=%s | job_type=%s | status=%s",
        job.id,
        job.job_type,
        job.status,
    )

    process_job.delay(str(job.id))
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

    process_job.delay(str(job.id))
    return job