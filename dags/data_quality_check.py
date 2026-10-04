"""Validate warehouse tables with Great Expectations and gate the marts layer."""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

GE_HOME = os.environ.get("GE_HOME", "/opt/airflow/quality/quality")
SUITE = os.environ.get("GE_SUITE", "sales")
SUITE_PATH = os.environ.get(
    "GE_SUITE_PATH",
    str(Path(__file__).resolve().parent.parent / "quality" / "expectations" / f"{SUITE}_suite.json"),
)

default_args = {
    "owner": "data-platform",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


def run_checkpoint() -> dict:
    import great_expectations as ge
    from great_expectations.checkpoint import Checkpoint
    from great_expectations.core.expectation_suite import ExpectationSuite
    from great_expectations.data_context.types.base import (
        DataContextConfig,
        InMemoryStoreBackendDefaults,
    )

    context = ge.get_context(
        project_config=DataContextConfig(
            store_backend_defaults=InMemoryStoreBackendDefaults(),
            datasources={
                "dataair": {
                    "class_name": "Datasource",
                    "module_name": "great_expectations.datasource",
                    "execution_engine": {
                        "class_name": "SqlAlchemyExecutionEngine",
                        "module_name": "great_expectations.execution_engine",
                        "connection_string": os.environ["WAREHOUSE_URL"],
                    },
                    "data_connectors": {
                        "warehouse": {
                            "class_name": "InferredAssetSqlDataConnector",
                            "module_name": "great_expectations.datasource.data_connector",
                            "include_schema_name": True,
                        }
                    },
                }
            },
        )
    )

    suite = ExpectationSuite(**json.loads(Path(SUITE_PATH).read_text()))
    context.add_or_update_expectation_suite(expectation_suite=suite)

    checkpoint = Checkpoint(
        name=f"{SUITE}_checkpoint",
        data_context=context,
        validations=[
            {
                "batch_request": {
                    "datasource_name": "dataair",
                    "data_connector_name": "warehouse",
                    "data_asset_name": f"marts.{SUITE}_daily",
                },
                "expectation_suite_name": f"{SUITE}_suite",
                "action_list": [
                    {
                        "name": "store_validation_result",
                        "action": {"class_name": "StoreValidationResultAction"},
                    },
                    {
                        "name": "store_evaluation_params",
                        "action": {"class_name": "StoreEvaluationParametersAction"},
                    },
                ],
            }
        ],
    )
    result = checkpoint.run()
    validations = []
    for run_result in result.run_results.values():
        validation = (
            run_result["validation_result"]
            if isinstance(run_result, dict)
            else run_result.validation_result
        )
        statistics = (
            validation.get("statistics", {})
            if isinstance(validation, dict)
            else validation.statistics
        )
        validations.append(
            {
                "success": bool(
                    validation.get("success", False)
                    if isinstance(validation, dict)
                    else validation.success
                ),
                "statistics": statistics,
            }
        )
    return {
        "success": bool(result.success),
        "suite_name": suite.expectation_suite_name,
        "validations": validations,
    }


def _fail_on_bad_quality(ti, **kwargs) -> None:
    results = ti.xcom_pull(task_ids="run_checkpoint") or {}
    if not results.get("success", False):
        failed = [
            v for v in results.get("validations", []) if not v.get("success", False)
        ]
        raise ValueError(f"{len(failed)} data quality validation(s) failed: {failed}")


with DAG(
    dag_id="data_quality_check",
    description="Great Expectations checkpoint against the warehouse",
    schedule_interval="30 3 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["quality", "great-expectations", "gating"],
) as dag:
    check = PythonOperator(
        task_id="run_checkpoint",
        python_callable=run_checkpoint,
        do_xcom_push=True,
    )

    gate = PythonOperator(
        task_id="enforce_quality_gate",
        python_callable=_fail_on_bad_quality,
    )

    audit = PostgresOperator(
        task_id="write_quality_audit",
        sql="""
            INSERT INTO audit.data_quality_results
                (run_id, suite_name, checkpoint_name, status, success, result)
            VALUES (
                '{{ dag_run.run_id }}',
                '{{ ti.xcom_pull(task_ids="run_checkpoint")["suite_name"] }}',
                'sales_checkpoint',
                'completed',
                {{ ti.xcom_pull(task_ids="run_checkpoint")["success"] }},
                '{{ (ti.xcom_pull(task_ids="run_checkpoint") | tojson | replace("'", "''")) }}'::jsonb
            );
        """,
    )

    check >> gate >> audit
