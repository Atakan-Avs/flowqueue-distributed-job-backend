from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.job import JobCreate, JobListResponse, JobResponse
from app.services.job_service import JobService
from app.tasks.job_tasks import process_job
from app.utils.enums import JobStatus
from fastapi import Depends
from app.core.rate_limit import rate_limiter

router = APIRouter()


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
        raise HTTPException(status_code=404, detail="Job not found")

    return job


@router.post("/jobs/{job_id}/retry", response_model=JobResponse)
def retry_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limiter),
):
    job, error = JobService.retry_job(db, job_id)

    if error == "not_found":
        raise HTTPException(status_code=404, detail="Job not found")

    if error == "processing":
        raise HTTPException(
            status_code=400,
            detail="Processing jobs cannot be retried",
        )

    process_job.delay(str(job.id))
    return job