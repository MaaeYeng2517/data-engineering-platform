#!/usr/bin/env bash
set -euo pipefail

command="${1:-webserver}"

ensure_connections() {
  airflow connections delete postgres_default >/dev/null 2>&1 || true
  airflow connections add postgres_default \
    --conn-uri "postgresql://${POSTGRES_USER:-dataair}:${POSTGRES_PASSWORD:-dataair}@postgres:5432/${POSTGRES_DB:-dataair}" >/dev/null 2>&1 || true
}

case "$command" in
  webserver)
    airflow db migrate
    ensure_connections
    if [ "${AIRFLOW_CREATE_ADMIN:-false}" = "true" ]; then
      airflow users create \
        --username "${AIRFLOW_ADMIN_USER:-admin}" \
        --password "${AIRFLOW_ADMIN_PASSWORD:-admin}" \
        --firstname DataAir \
        --lastname Admin \
        --role Admin \
        --email "${AIRFLOW_ADMIN_EMAIL:-admin@dataair.local}" || true
    fi
    exec airflow webserver --port 8080
    ;;
  scheduler)
    ensure_connections
    exec airflow scheduler
    ;;
  worker)
    exec airflow celery --pool "${AIRFLOW_CELERY_POOL:-default_pool}"
    ;;
  triggerer)
    exec airflow triggerer
    ;;
  standalone)
    exec airflow standalone
    ;;
  *)
    exec airflow "$@"
    ;;
esac
