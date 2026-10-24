from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "enterprise_data_api",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.task_routes = {
    "app.workers.tasks_ingestion.*": {"queue": "ingestion"},
    "app.workers.tasks_transform.*": {"queue": "transform"},
    "app.workers.tasks_quality.*": {"queue": "quality"},
}
celery_app.conf.task_default_retry_delay = 60
celery_app.conf.task_max_retries = 3
