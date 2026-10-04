"""Land raw objects from MinIO into the raw schema, then hand off to dbt."""

import io
import os
from datetime import datetime, timedelta

import boto3
import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator

LANDING_SCHEMA = os.environ.get("RAW_SCHEMA", "raw")
LANDING_BUCKET = os.environ.get("MINIO_BUCKET", "dataair")

TABLES = {
    "sales.csv": "raw.sales",
    "products.csv": "raw.products",
    "customers.csv": "raw.customers",
}

default_args = {
    "owner": "data-platform",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


def _client() -> boto3.client:
    return boto3.client(
        "s3",
        endpoint_url=f"http://{os.environ.get('MINIO_ENDPOINT', 'minio:9000')}",
        aws_access_key_id=os.environ["MINIO_ACCESS_KEY"],
        aws_secret_access_key=os.environ["MINIO_SECRET_KEY"],
    )


def list_objects() -> list:
    client = _client()
    paginator = client.get_paginator("list_objects_v2")
    keys: list = []
    for page in paginator.paginate(Bucket=LANDING_BUCKET):
        keys.extend(obj["Key"] for obj in page.get("Contents", []))
    return keys


def land_tables():
    client = _client()
    imported = []
    for filename, target in TABLES.items():
        try:
            body = client.get_object(Bucket=LANDING_BUCKET, Key=filename)["Body"].read()
        except client.exceptions.NoSuchKey:
            continue

        frame = pd.read_csv(io.BytesIO(body))
        _write_frame(target, frame)
        imported.append({"table": target, "rows": len(frame)})
    return imported


def _write_frame(target_table: str, frame: pd.DataFrame) -> None:
    from sqlalchemy import create_engine, text

    engine = create_engine(os.environ["WAREHOUSE_URL"])
    raw_frame = frame.assign(_ingested_at=pd.Timestamp.utcnow())
    raw_frame.to_sql(
        target_table.split(".")[1],
        engine,
        schema=target_table.split(".")[0],
        if_exists="append",
        index=False,
    )
    with engine.begin() as conn:
        conn.execute(text(f"ANALYZE {target_table}"))


def reconcile() -> int:
    from sqlalchemy import create_engine, text

    engine = create_engine(os.environ["WAREHOUSE_URL"])
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT count(*) FROM raw.sales")
        ).scalar_one()
    print(f"raw.sales now holds {rows} rows")
    return int(rows)


with DAG(
    dag_id="ingest_minio_landing",
    description="Extract raw files from MinIO into the raw schema",
    schedule_interval="*/30 * * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["ingestion", "minio", "raw"],
) as dag:
    inventory = PythonOperator(
        task_id="list_objects",
        python_callable=list_objects,
    )

    land = PythonOperator(
        task_id="land_tables",
        python_callable=land_tables,
    )

    audit = PostgresOperator(
        task_id="write_ingest_audit",
        sql="""
            INSERT INTO audit.elt_runs (run_id, model_name, layer, status, finished_at)
            VALUES ('{{ dag_run.run_id }}', 'minio_landing', 'raw', 'success', NOW());
        """,
    )

    inventory >> land >> audit
