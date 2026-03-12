from kombu import Queue

from app.core.config import settings
from app.core.logging import setup_logging
from celery import Celery

setup_logging()

celery_app = Celery(
    "flowqueue",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.tasks.job_tasks"],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Istanbul",
    enable_utc=False,
    task_default_queue="normal",
    task_queues=(
        Queue("high"),
        Queue("normal"),
        Queue("low"),
    ),
)