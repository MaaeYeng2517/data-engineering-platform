"""Entrypoint for the Celery beat scheduler.

Wraps the standard `celery beat` command so the process also exposes a
Prometheus endpoint on :9100, scraped by the `scheduler` job.
"""
import logging
import os

from prometheus_client import start_http_server

from backend.app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

METRICS_PORT = int(os.getenv("CELERY_METRICS_PORT", "9100"))


def main() -> None:
    """Expose metrics, then hand control to Celery's beat scheduler."""
    start_http_server(METRICS_PORT)
    logger.info("Celery beat metrics listening on :%d", METRICS_PORT)
    # Celery passes this list straight to click, so it must not include argv[0].
    celery_app.start(argv=["beat", "--loglevel=info"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()