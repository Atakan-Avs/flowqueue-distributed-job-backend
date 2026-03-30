import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.core.metrics import jobs_created_total
from app.core.rate_limit import rate_limiter
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.job import JobCreate, JobListResponse, JobResponse
from app.schemas.metrics import JobMetricsResponse
from app.services.job_service import JobService
from app.tasks.job_tasks import process_job
from app.utils.enums import JobPriority, JobStatus, UserRole

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/jobs", response_model=JobResponse, status_code=201)
def create_job(
    job_data: JobCreate,
    db: Session = Depends(get_db),
    _: None = Depends(rate_limiter),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN.value, UserRole.OPERATOR.value)
    ),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    valid_priorities = {item.value for item in JobPriority}
    if job_data.priority not in valid_priorities:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid priority. Allowed values: {', '.join(valid_priorities)}",
        )

    normalized_idempotency_key = idempotency_key.strip() if idempotency_key else None
    if normalized_idempotency_key == "":
        normalized_idempotency_key = None

    job, created = JobService.create_job(
        db=db,
        job_type=job_data.job_type,
        payload=job_data.payload,
        priority=job_data.priority,
        idempotency_key=normalized_idempotency_key,
    )

    if created:
        jobs_created_total.inc()
        logger.info(
            "Job created and queued | user_id=%s | job_id=%s | job_type=%s | status=%s | priority=%s | idempotency_key=%s",
            current_user.id,
            job.id,
            job.job_type,
            job.status,
            job.priority,
            job.idempotency_key,
        )
        process_job.apply_async(args=[str(job.id)], queue=job.priority)
    else:
        logger.info(
            "Duplicate job prevented by idempotency key | user_id=%s | job_id=%s | idempotency_key=%s",
            current_user.id,
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
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN.value,
            UserRole.OPERATOR.value,
            UserRole.VIEWER.value,
        )
    ),
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
        "Jobs listed | user_id=%s | total=%s | skip=%s | limit=%s | status_filter=%s",
        current_user.id,
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
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN.value,
            UserRole.OPERATOR.value,
            UserRole.VIEWER.value,
        )
    ),
):
    items, total = JobService.list_dead_letter_jobs(
        db=db,
        skip=skip,
        limit=limit,
    )

    logger.info(
        "Dead letter jobs listed | user_id=%s | total=%s | skip=%s | limit=%s",
        current_user.id,
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
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN.value,
            UserRole.OPERATOR.value,
            UserRole.VIEWER.value,
        )
    ),
):
    job = JobService.get_job(db, job_id)

    if not job:
        logger.warning(
            "Job not found | user_id=%s | job_id=%s",
            current_user.id,
            job_id,
        )
        raise HTTPException(status_code=404, detail="Job not found")

    logger.info(
        "Job retrieved | user_id=%s | job_id=%s | status=%s | retry_count=%s",
        current_user.id,
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
    current_user: User = Depends(
        require_roles(UserRole.ADMIN.value, UserRole.OPERATOR.value)
    ),
):
    job, error = JobService.retry_job(db, job_id)

    if error == "not_found":
        logger.warning(
            "Retry failed - job not found | user_id=%s | job_id=%s",
            current_user.id,
            job_id,
        )
        raise HTTPException(status_code=404, detail="Job not found")

    if error == "processing":
        logger.warning(
            "Retry rejected - job still processing | user_id=%s | job_id=%s",
            current_user.id,
            job_id,
        )
        raise HTTPException(
            status_code=400,
            detail="Processing jobs cannot be retried",
        )

    if error == "completed":
        logger.warning(
            "Retry rejected - job already completed | user_id=%s | job_id=%s",
            current_user.id,
            job_id,
        )
        raise HTTPException(
            status_code=400,
            detail="Completed jobs cannot be retried",
        )

    if error == "dead_letter":
        logger.warning(
            "Retry rejected - dead letter job must be requeued | user_id=%s | job_id=%s",
            current_user.id,
            job_id,
        )
        raise HTTPException(
            status_code=400,
            detail="Dead letter jobs must be requeued instead of retried",
        )

    if error == "invalid_status":
        logger.warning(
            "Retry rejected - only failed jobs can be retried | user_id=%s | job_id=%s",
            current_user.id,
            job_id,
        )
        raise HTTPException(
            status_code=400,
            detail="Only failed jobs can be retried",
        )

    logger.info(
        "Job retry triggered and queued | user_id=%s | job_id=%s | retry_count=%s",
        current_user.id,
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
    current_user: User = Depends(
        require_roles(UserRole.ADMIN.value, UserRole.OPERATOR.value)
    ),
):
    job, error = JobService.requeue_dead_letter_job(db, job_id)

    if error == "not_found":
        logger.warning(
            "Requeue failed - job not found | user_id=%s | job_id=%s",
            current_user.id,
            job_id,
        )
        raise HTTPException(status_code=404, detail="Job not found")

    if error == "not_dead_letter":
        logger.warning(
            "Requeue rejected - job is not in dead letter queue | user_id=%s | job_id=%s",
            current_user.id,
            job_id,
        )
        raise HTTPException(status_code=400, detail="Job is not in dead letter queue")

    logger.info(
        "Dead letter job requeued | user_id=%s | job_id=%s | priority=%s",
        current_user.id,
        job.id,
        job.priority,
    )

    process_job.apply_async(args=[str(job.id)], queue=job.priority)
    return job


@router.get("/metrics/jobs", response_model=JobMetricsResponse)
def job_metrics(
    db: Session = Depends(get_db),
    _: None = Depends(rate_limiter),
    current_user: User = Depends(
        require_roles(
            UserRole.ADMIN.value,
            UserRole.OPERATOR.value,
            UserRole.VIEWER.value,
        )
    ),
):
    metrics = JobService.get_metrics(db)

    logger.info(
        "Job metrics retrieved | user_id=%s | total_jobs=%s | pending=%s | processing=%s | completed=%s | failed=%s",
        current_user.id,
        metrics["total_jobs"],
        metrics["pending"],
        metrics["processing"],
        metrics["completed"],
        metrics["failed"],
    )

    return metrics