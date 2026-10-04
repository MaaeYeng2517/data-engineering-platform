"""Run the dbt project that builds the medallion warehouse."""

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

PROJECT_DIR = os.environ.get("DBT_PROJECT_DIR", "/opt/airflow/dbt")
DBT_BIN = os.environ.get("DBT_BIN", "/opt/dbt-venv/bin/dbt")

DAG_ID = "warehouse_build"

default_args = {
    "owner": "data-platform",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id=DAG_ID,
    description="dbt build across raw -> staging -> marts",
    schedule_interval="0 2 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["dbt", "warehouse", "elt"],
) as dag:
    dbt_clean = BashOperator(
        task_id="dbt_clean",
        bash_command=f"cd {PROJECT_DIR} && {DBT_BIN} clean --profiles-dir {PROJECT_DIR}",
        doc_md="Drop stale target/ and dbt_packages/ artifacts.",
    )

    dbt_deps = BashOperator(
        task_id="dbt_deps",
        bash_command=f"cd {PROJECT_DIR} && {DBT_BIN} deps --profiles-dir {PROJECT_DIR}",
        doc_md="Install dbt packages declared in packages.yml.",
    )

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            f"cd {PROJECT_DIR} && {DBT_BIN} build "
            f"--profiles-dir {PROJECT_DIR} "
            f"--target {{{{ dag_run.conf.get('dbt_target', 'prod') if dag_run else 'prod' }}}} "
            "--vars '{\"run_id\": \"{{ dag_run.run_id }}\"}'"
        ),
        doc_md="dbt build runs models, tests and snapshots in DAG order.",
        execution_timeout=timedelta(hours=4),
    )

    audit = PostgresOperator(
        task_id="record_run",
        sql="""
            INSERT INTO audit.elt_runs (run_id, model_name, layer, status, finished_at)
            VALUES (
                '{{ dag_run.run_id }}',
                'dbt_build',
                'all',
                'success',
                NOW()
            );
        """,
    )

    dbt_clean >> dbt_deps >> dbt_build >> audit
