"""Publish lineage and run metadata to OpenMetadata, and check data freshness."""

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

OPENMETADATA_URL = os.environ.get("OPENMETADATA_URL", "http://openmetadata:8585")

default_args = {
    "owner": "data-platform",
    "retries": 1,
    "retry_delay": timedelta(minutes=10),
}


def push_lineage() -> str:
    # Lineage publication is handled by the openmetadata-ingestion service
    # (docker/openmetadata/workflows.yaml); this task keeps the DAG slot and
    # verifies the catalog API is reachable.
    import httpx

    response = httpx.get(f"{OPENMETADATA_URL}/api/v1/system/version", timeout=10)
    response.raise_for_status()
    return f"catalog reachable: {response.json().get('version')}"


def check_freshness(threshold_hours: int = 30) -> None:
    from sqlalchemy import create_engine, text

    engine = create_engine(os.environ["WAREHOUSE_URL"])
    with engine.begin() as conn:
        stale = conn.execute(
            text(
                """
                SELECT model_name, max(finished_at) AS last_success
                FROM audit.elt_runs
                WHERE status = 'success'
                GROUP BY model_name
                HAVING max(finished_at) < NOW() - make_interval(hours => :threshold)
                """
            ),
            {"threshold": threshold_hours},
        ).fetchall()

    if stale:
        raise ValueError(f"Stale models detected: {stale}")


with DAG(
    dag_id="catalog_sync",
    description="Publish lineage to OpenMetadata and verify model freshness",
    schedule_interval="0 4 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["catalog", "lineage", "openmetadata", "freshness"],
) as dag:
    lineage = PythonOperator(
        task_id="emit_lineage",
        python_callable=push_lineage,
    )

    freshness = PythonOperator(
        task_id="check_freshness",
        python_callable=check_freshness,
        op_kwargs={"threshold_hours": 30},
    )

    audit = PostgresOperator(
        task_id="record_catalog_sync",
        sql="""
            INSERT INTO audit.elt_runs (run_id, model_name, layer, status, finished_at)
            VALUES ('{{ dag_run.run_id }}', 'openmetadata_lineage', 'audit', 'success', NOW());
        """,
    )

    lineage >> freshness >> audit
