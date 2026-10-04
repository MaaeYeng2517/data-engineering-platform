"""Entrypoint for the Celery worker process."""
import logging
import os

from prometheus_client import start_http_server

from backend.app.observability import configure_telemetry
from backend.app.workers.celery_app import celery_app
from backend.app.workers import tasks  # noqa: F401  (registers the task modules)

logger = logging.getLogger(__name__)

CONCURRENCY = int(os.getenv("CELERY_CONCURRENCY", "2"))
METRICS_PORT = int(os.getenv("CELERY_METRICS_PORT", "9100"))


def main() -> None:
    """Start the worker with the queues declared in the Celery config."""
    configure_telemetry()
    # Prometheus scrapes this endpoint on the `celery-worker` job.
    start_http_server(METRICS_PORT)
    logger.info("Celery metrics listening on :%d", METRICS_PORT)
    celery_app.worker_main(
        [
            "worker",
            f"--concurrency={CONCURRENCY}",
            "--loglevel=info",
            "--queues=default,indexing,ingestion,celery",
            "--hostname=worker@%h",
        ]
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()