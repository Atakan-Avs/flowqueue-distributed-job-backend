import logging

from app.core.celery_app import celery_app
from app.core.metrics import jobs_created_total
from app.tasks.job_tasks import process_job
from app.tasks.scheduled_tasks import create_scheduled_job

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.beat_tasks.enqueue_scheduled_report")
def enqueue_scheduled_report():
    job_id = create_scheduled_job()
    jobs_created_total.inc()

    logger.info(
        "Scheduled job created by Celery Beat | job_id=%s | job_type=%s",
        job_id,
        "scheduled_report",
    )

    process_job.apply_async(args=[job_id], queue="normal")