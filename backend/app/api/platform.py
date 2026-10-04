"""Platform integration API — exposes every connected system to the frontend."""
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.services.platform import airflow, minio_storage, openmetadata, prometheus, warehouse
from backend.app.services.platform.status import get_system_status

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/platform/health")
async def platform_health() -> Dict[str, Any]:
    return await get_system_status()


# --- Warehouse -------------------------------------------------------------

@router.get("/warehouse/sales")
async def sales_daily(limit: int = Query(120, ge=1, le=1000)):
    return await warehouse.get_sales_daily(limit=limit)


@router.get("/warehouse/sales/summary")
async def sales_summary():
    return await warehouse.get_sales_summary()


@router.get("/warehouse/products/top")
async def top_products(limit: int = Query(10, ge=1, le=100)):
    return await warehouse.get_top_products(limit=limit)


@router.get("/warehouse/categories")
async def category_breakdown():
    return await warehouse.get_category_breakdown()


@router.get("/warehouse/elt-runs")
async def elt_runs(limit: int = Query(50, ge=1, le=500)):
    return await warehouse.get_elt_runs(limit=limit)


@router.get("/warehouse/quality")
async def quality_results(limit: int = Query(20, ge=1, le=200)):
    return await warehouse.get_quality_results(limit=limit)


@router.get("/warehouse/tables")
async def warehouse_tables():
    return await warehouse.get_warehouse_overview()


# --- Airflow pipelines -----------------------------------------------------

@router.get("/pipelines/dags")
async def list_dags(limit: int = Query(100, ge=1, le=500)):
    return await airflow.list_dags(limit=limit)


@router.get("/pipelines/dags/{dag_id}")
async def get_dag(dag_id: str):
    dag = await airflow.get_dag(dag_id)
    if not dag:
        raise HTTPException(status_code=404, detail="DAG not found")
    return dag


@router.get("/pipelines/dags/{dag_id}/runs")
async def dag_runs(dag_id: str, limit: int = Query(25, ge=1, le=200)):
    return await airflow.list_dag_runs(dag_id, limit=limit)


@router.get("/pipelines/dags/{dag_id}/runs/{run_id}/tasks")
async def dag_run_tasks(dag_id: str, run_id: str):
    return await airflow.get_dag_run_task_instances(dag_id, run_id)


@router.post("/pipelines/dags/{dag_id}/trigger")
async def trigger_dag(dag_id: str, conf: Optional[Dict[str, Any]] = None):
    result = await airflow.trigger_dag(dag_id, conf=conf)
    if not result:
        raise HTTPException(status_code=502, detail="Failed to trigger DAG")
    return result


@router.patch("/pipelines/dags/{dag_id}/pause")
async def pause_dag(dag_id: str, paused: bool = True):
    result = await airflow.set_dag_pause(dag_id, paused)
    if not result:
        raise HTTPException(status_code=502, detail="Failed to update DAG")
    return result


# --- OpenMetadata catalog --------------------------------------------------

@router.get("/catalog/tables")
async def catalog_tables(limit: int = Query(50, ge=1, le=500)):
    return await openmetadata.list_tables(limit=limit)


@router.get("/catalog/search")
async def catalog_search(q: str = Query(..., min_length=1), limit: int = Query(20, ge=1, le=100)):
    return await openmetadata.search_catalog(q, limit=limit)


@router.get("/catalog/lineage/{table_fqn:path}")
async def table_lineage(table_fqn: str):
    lineage = await openmetadata.get_table_lineage(table_fqn)
    if lineage is None:
        raise HTTPException(status_code=404, detail="Lineage not found")
    return lineage


@router.get("/catalog/glossary")
async def glossary_terms(limit: int = Query(50, ge=1, le=500)):
    return await openmetadata.list_glossary_terms(limit=limit)


# --- Object storage --------------------------------------------------------

@router.get("/storage/buckets")
async def storage_buckets():
    return await minio_storage.list_buckets()


@router.get("/storage/objects")
async def storage_objects(
    bucket: Optional[str] = Query(None),
    prefix: str = Query(""),
    limit: int = Query(100, ge=1, le=1000),
):
    return await minio_storage.list_objects(bucket=bucket, prefix=prefix, limit=limit)


@router.get("/storage/stats")
async def storage_stats():
    return await minio_storage.get_bucket_stats()


# --- Monitoring ------------------------------------------------------------

@router.get("/monitoring/query")
async def monitoring_query(q: str = Query(..., min_length=1)):
    return await prometheus.instant_query(q)


@router.get("/monitoring/range")
async def monitoring_range(q: str = Query(..., min_length=1), hours: float = Query(24.0, ge=0.5, le=720.0)):
    return await prometheus.range_query(q, hours=hours)


@router.get("/monitoring/summary")
async def monitoring_summary():
    return await prometheus.get_platform_summary()


# --- Links to external UIs -------------------------------------------------

@router.get("/links")
async def platform_links() -> Dict[str, Any]:
    from backend.config import (
        AIRFLOW_PUBLIC_URL,
        GRAFANA_PUBLIC_URL,
        OPENMETADATA_PUBLIC_URL,
        PROMETHEUS_PUBLIC_URL,
    )

    return {
        "airflow": AIRFLOW_PUBLIC_URL,
        "openmetadata": OPENMETADATA_PUBLIC_URL,
        "prometheus": PROMETHEUS_PUBLIC_URL,
        "grafana": GRAFANA_PUBLIC_URL,
    }
