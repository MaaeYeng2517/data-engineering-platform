"""Celery application used by the worker, beat scheduler and Flower."""
import logging
import os

from celery import Celery
from celery.schedules import crontab

from backend.config import REDIS_URL

logger = logging.getLogger(__name__)

BROKER_URL = os.getenv("CELERY_BROKER_URL", REDIS_URL)
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", REDIS_URL)

celery_app = Celery("dataair", broker=BROKER_URL, backend=RESULT_BACKEND)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone=os.getenv("CELERY_TIMEZONE", "UTC"),
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="default",
    task_routes={
        "dataair.index.*": {"queue": "indexing"},
        "dataair.ingest.*": {"queue": "ingestion"},
    },
    beat_schedule={
        "refresh-active-tenants": {
            "task": "dataair.maintenance.refresh_active_tenants",
            "schedule": crontab(minute="*/15"),
        },
    },
    broker_connection_retry_on_startup=True,
)

celery_app.autodiscover_tasks(["backend.app.workers"], related_name="tasks", force=True)


@celery_app.task(name="dataair.maintenance.refresh_active_tenants")
def refresh_active_tenants() -> dict:
    """Periodic no-op placeholder that keeps the beat schedule valid."""
    logger.debug("Maintenance tick executed")
    return {"status": "ok"}