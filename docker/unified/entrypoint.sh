#!/usr/bin/env bash
# Role dispatcher for the unified data-engineering-platform image.
#
# One image carries the API, the Celery worker, Airflow, dbt, the Jupyter toolbox
# and the Next.js server, so the container has to know which of those it is. Set
# PLATFORM_ROLE (or pass it as the first argument) and this script execs the
# right binary in the right virtualenv.
set -euo pipefail

ROLE="${1:-${PLATFORM_ROLE:-}}"
if [ $# -gt 0 ]; then
  shift
fi

APP_HOME=/app
AIRFLOW_VENV=/opt/airflow-venv
DBT_VENV=/opt/dbt-venv
WEB_HOME=/opt/web

cd "$APP_HOME"

log() { printf '[unified] %s\n' "$*"; }

case "$ROLE" in
  # --- API and queue workers: the backend's own environment ---
  backend)
    exec uvicorn backend.main:app --host 0.0.0.0 --port "${BACKEND_PORT:-8000}" "$@"
    ;;
  worker)
    exec python -m backend.app.workers.celery_worker "$@"
    ;;
  scheduler)
    exec python -m backend.app.workers.celery_beat "$@"
    ;;
  flower)
    exec celery -A backend.app.workers.celery_app flower \
      --port="${FLOWER_PORT:-5555}" --broker="${CELERY_BROKER_URL:-redis://redis:6379/0}" "$@"
    ;;

  # --- Airflow: pinned separately so its constraints hold ---
  airflow-webserver)
    exec "$AIRFLOW_VENV/bin/airflow" webserver "$@"
    ;;
  airflow-scheduler)
    exec "$AIRFLOW_VENV/bin/airflow" scheduler "$@"
    ;;
  airflow-triggerer)
    exec "$AIRFLOW_VENV/bin/airflow" triggerer "$@"
    ;;
  airflow-init)
    exec "$AIRFLOW_VENV/bin/airflow" db migrate "$@"
    ;;

  # --- Toolbox ---
  dbt)
    # dbt reads its profiles from DBT_PROFILES_DIR; run it against the project.
    export DBT_PROFILES_DIR="${DBT_PROFILES_DIR:-/app/dbt}"
    exec "$DBT_VENV/bin/dbt" "$@"
    ;;
  jupyter)
    exec jupyter lab --ip=0.0.0.0 --port="${JUPYTER_PORT:-8888}" \
      --notebook-dir=/app/notebooks --no-browser "$@"
    ;;
  great-expectations)
    exec great_expectations "$@"
    ;;

  # --- Web ---
  web)
    cd "$WEB_HOME"
    exec node server.js "$@"
    ;;

  # --- Operations ---
  shell)
    exec /bin/bash "$@"
    ;;
  test)
    exec python -m pytest tests/ -v "$@"
    ;;
  lint)
    exec ruff check backend tests workers dags "$@"
    ;;
  '' )
    log "No role given. Set PLATFORM_ROLE or pass one of:"
    log "  API        backend | worker | scheduler | flower"
    log "  Airflow    airflow-webserver | airflow-scheduler | airflow-triggerer | airflow-init"
    log "  Toolbox    dbt | jupyter | great-expectations"
    log "  Web        web"
    log "  Ops        shell | test | lint"
    exit 2
    ;;
  *)
    # Anything else runs verbatim, so the image stays usable as a plain tool
    # runner: `docker run --rm <image> python -V`.
    exec "$ROLE" "$@"
    ;;
esac