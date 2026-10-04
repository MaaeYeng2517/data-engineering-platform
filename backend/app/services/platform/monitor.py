"""Live monitoring for every service that makes up the DataAir stack.

The dashboard status page reads from here. Each service is probed from inside
the backend container, so checks reflect real connectivity over the compose
network rather than browser reachability.
"""
import asyncio
import time
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy import text

from backend.config import (
    AIRFLOW_PUBLIC_URL,
    AIRFLOW_URL,
    ELASTICSEARCH_URL,
    GRAFANA_PUBLIC_URL,
    GRAFANA_URL,
    MINIO_ENDPOINT,
    OPENMETADATA_PUBLIC_URL,
    OPENMETADATA_URL,
    PROMETHEUS_PUBLIC_URL,
    PROMETHEUS_URL,
    QDRANT_URL,
    REDIS_URL,
)
from backend.database import async_session_factory

CATEGORY_LABELS = {
    "data": "Data Layer",
    "app": "Application",
    "orchestration": "Orchestration",
    "observability": "Observability",
    "catalog": "Catalog",
    "tooling": "Tooling",
}

STATUS_HEALTHY = "healthy"
STATUS_DEGRADED = "degraded"
STATUS_DOWN = "down"

_HTTP_TIMEOUT = 8.0


async def _timed_http(
    url: str,
    label: str,
    success: int = 200,
    accept: tuple = (200, 201, 204, 301, 302, 401, 403),
    detail: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT, verify=False) as client:
            response = await client.get(url, headers=headers or {})
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        if response.status_code not in accept:
            return {
                "status": STATUS_DEGRADED,
                "detail": f"HTTP {response.status_code} · {detail}" if detail else f"HTTP {response.status_code}",
                "latency_ms": latency_ms,
                "http_status": response.status_code,
            }
        info: Dict[str, Any] = {
            "status": STATUS_HEALTHY,
            "detail": detail or f"HTTP {response.status_code}",
            "latency_ms": latency_ms,
            "http_status": response.status_code,
        }
        info.update(_summarize_body(label, response))
        return info
    except Exception as exc:
        return {
            "status": STATUS_DOWN,
            "detail": f"{type(exc).__name__}: {exc}"[:180],
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }


def _summarize_body(label: str, response: httpx.Response) -> Dict[str, Any]:
    """Pull one human-readable fact out of a health payload."""
    try:
        data = response.json()
    except Exception:
        return {}

    if label == "elasticsearch":
        shards = data.get("active_shards")
        nodes = data.get("number_of_nodes")
        return {"detail": f"{data.get('status')} · {shards} shards · {nodes} node(s)"}
    if label == "openmetadata":
        return {"detail": f"OpenMetadata {data.get('version')}"}
    if label == "grafana":
        return {"detail": f"database={data.get('database')} · v{data.get('version')}"}
    if label == "prometheus_targets":
        active = (data.get("data") or {}).get("activeTargets", [])
        up = sum(1 for t in active if t.get("health") == "up")
        return {"detail": f"{up}/{len(active)} targets up", "targets": _target_rows(active)}
    return {}


def _target_rows(active: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    rows = []
    for target in active:
        rows.append(
            {
                "job": target.get("labels", {}).get("job", "?"),
                "health": target.get("health", "unknown"),
                "error": (target.get("lastError") or "")[:120],
            }
        )
    return sorted(rows, key=lambda row: row["job"])


async def check_postgres() -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        async with async_session_factory() as db:
            result = await db.execute(
                text(
                    "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
            )
            tables = result.scalar() or 0
            version = (await db.execute(text("SHOW server_version"))).scalar()
            databases = (
                await db.execute(
                    text("SELECT datname FROM pg_database WHERE datistemplate = false")
                )
            ).scalars().all()
        return {
            "status": STATUS_HEALTHY,
            "detail": f"PostgreSQL {version} · {tables} tables",
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
            "databases": sorted(databases),
        }
    except Exception as exc:
        return {"status": STATUS_DOWN, "detail": f"{type(exc).__name__}: {exc}"[:180]}


async def check_redis() -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(REDIS_URL, socket_timeout=5)
        try:
            await client.ping()
            info = await client.info("server")
            keys = await client.dbsize()
        finally:
            await client.aclose()
        return {
            "status": STATUS_HEALTHY,
            "detail": f"Redis {info.get('redis_version')} · {keys} keys",
            "latency_ms": round((time.perf_counter() - started) * 1000, 1),
        }
    except Exception as exc:
        return {"status": STATUS_DOWN, "detail": f"{type(exc).__name__}: {exc}"[:180]}


async def check_minio() -> Dict[str, Any]:
    host, _, port = MINIO_ENDPOINT.partition(":")
    url = f"http://{host}:{port or '9000'}"
    return await _timed_http(f"{url}/minio/health/live", "minio", detail="S3 API")


async def check_elasticsearch() -> Dict[str, Any]:
    return await _timed_http(f"{ELASTICSEARCH_URL}/_cluster/health", "elasticsearch")


async def check_qdrant() -> Dict[str, Any]:
    return await _timed_http(f"{QDRANT_URL}/collections", "qdrant")


async def check_backend() -> Dict[str, Any]:
    return await _timed_http("http://localhost:8000/health", "backend", detail="FastAPI")


async def check_frontend() -> Dict[str, Any]:
    return await _timed_http("http://frontend:3000/", "frontend", detail="Next.js")


async def check_nginx() -> Dict[str, Any]:
    return await _timed_http("http://nginx/health", "nginx", detail="reverse proxy → backend")


async def check_airflow_webserver() -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=_HTTP_TIMEOUT) as client:
            response = await client.get(f"{AIRFLOW_URL}/health")
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        if response.status_code != 200:
            return {
                "status": STATUS_DOWN,
                "detail": f"HTTP {response.status_code}",
                "latency_ms": latency_ms,
            }
        data = response.json()
        meta = (data.get("metadatabase") or {}).get("status", "?")
        scheduler = (data.get("scheduler") or {}).get("status", "?")
        triggerer = (data.get("triggerer") or {}).get("status", "n/a")
        healthy = meta == "healthy" and scheduler == "healthy"
        return {
            "status": STATUS_HEALTHY if healthy else STATUS_DEGRADED,
            "detail": f"metadatabase={meta} · scheduler={scheduler} · triggerer={triggerer}",
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        return {"status": STATUS_DOWN, "detail": f"{type(exc).__name__}: {exc}"[:180]}


async def check_airflow_internal() -> Dict[str, Any]:
    """DAG inventory proves scheduler and triggerer are still processing."""
    from backend.app.services.platform import airflow as airflow_service

    started = time.perf_counter()
    try:
        dags = await airflow_service.list_dags(limit=100)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {
            "status": STATUS_HEALTHY if dags else STATUS_DEGRADED,
            "detail": f"{len(dags)} DAGs loaded by scheduler",
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        return {"status": STATUS_DOWN, "detail": f"{type(exc).__name__}: {exc}"[:180]}


async def check_celery_worker() -> Dict[str, Any]:
    return await _celery_control_ping()


async def check_celery_scheduler() -> Dict[str, Any]:
    return await _celery_control_ping()


async def _celery_control_ping() -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        from backend.app.workers.celery_app import celery_app

        # `control.ping` blocks the calling thread while it waits for replies, so it
        # must not run on the event loop — one blocked loop starves every other probe.
        def _ping() -> list:
            return list(celery_app.control.ping(timeout=5) or [])

        replies = await asyncio.wait_for(asyncio.to_thread(_ping), timeout=10)
        latency_ms = round((time.perf_counter() - started) * 1000, 1)
        return {
            "status": STATUS_HEALTHY if replies else STATUS_DOWN,
            "detail": f"{len(replies)} worker(s) replied to ping" if replies else "no worker replied",
            "latency_ms": latency_ms,
        }
    except Exception as exc:
        return {"status": STATUS_DOWN, "detail": f"{type(exc).__name__}: {exc}"[:180]}


async def check_flower() -> Dict[str, Any]:
    return await _timed_http("http://flower:5555/", "flower", detail="Celery monitor")


async def check_openmetadata() -> Dict[str, Any]:
    return await _timed_http(
        f"{OPENMETADATA_URL}/api/v1/system/version", "openmetadata"
    )


async def check_prometheus() -> Dict[str, Any]:
    health = await _timed_http(f"{PROMETHEUS_URL}/-/healthy", "prometheus")
    if health["status"] != STATUS_HEALTHY:
        return health
    targets = await _timed_http(
        f"{PROMETHEUS_URL}/api/v1/targets?state=active", "prometheus_targets"
    )
    health.update(
        {k: v for k, v in targets.items() if k in {"detail", "targets"}}
    )
    if targets.get("targets"):
        down = [t["job"] for t in targets["targets"] if t["health"] != "up"]
        if down:
            health["status"] = STATUS_DEGRADED
            health["detail"] = f"{targets['detail']} · down: {', '.join(down)}"
    return health


async def check_grafana() -> Dict[str, Any]:
    return await _timed_http(f"{GRAFANA_URL}/api/health", "grafana")


async def check_jupyter() -> Dict[str, Any]:
    return await _timed_http("http://python:8888/api", "jupyter", detail="JupyterLab")


SERVICE_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "postgres",
        "name": "postgres",
        "tools": "PostgreSQL 16 · pgvector",
        "port": "5432",
        "category": "data",
        "public_url": None,
        "checker": check_postgres,
    },
    {
        "id": "redis",
        "name": "redis",
        "tools": "Redis 7.2",
        "port": "6379",
        "category": "data",
        "public_url": None,
        "checker": check_redis,
    },
    {
        "id": "minio",
        "name": "minio",
        "tools": "MinIO · S3 API",
        "port": "9000 / 9001",
        "category": "data",
        "public_url": "http://localhost:9001",
        "checker": check_minio,
    },
    {
        "id": "elasticsearch",
        "name": "elasticsearch",
        "tools": "Elasticsearch 8.17",
        "port": "9200",
        "category": "data",
        "public_url": "http://localhost:9200",
        "checker": check_elasticsearch,
    },
    {
        "id": "qdrant",
        "name": "qdrant",
        "tools": "Qdrant 1.12",
        "port": "6333 / 6334",
        "category": "data",
        "public_url": "http://localhost:6333",
        "checker": check_qdrant,
    },
    {
        "id": "backend",
        "name": "backend",
        "tools": "FastAPI · uvicorn",
        "port": "8000",
        "category": "app",
        "public_url": "http://localhost:8000/docs",
        "checker": check_backend,
    },
    {
        "id": "frontend",
        "name": "frontend",
        "tools": "Next.js 14 · Node 20",
        "port": "3000",
        "category": "app",
        "public_url": "http://localhost:3000",
        "checker": check_frontend,
    },
    {
        "id": "nginx",
        "name": "nginx",
        "tools": "nginx:alpine",
        "port": "80 / 443",
        "category": "app",
        "public_url": "http://localhost",
        "checker": check_nginx,
    },
    {
        "id": "airflow-webserver",
        "name": "airflow-webserver",
        "tools": "Apache Airflow 2.10.3",
        "port": "8080",
        "category": "orchestration",
        "public_url": AIRFLOW_PUBLIC_URL,
        "checker": check_airflow_webserver,
    },
    {
        "id": "airflow-scheduler",
        "name": "airflow-scheduler",
        "tools": "Airflow scheduler",
        "port": "internal 8080",
        "category": "orchestration",
        "public_url": None,
        "checker": check_airflow_internal,
    },
    {
        "id": "airflow-triggerer",
        "name": "airflow-triggerer",
        "tools": "Airflow triggerer",
        "port": "internal 8080",
        "category": "orchestration",
        "public_url": None,
        "checker": check_airflow_internal,
    },
    {
        "id": "worker",
        "name": "worker",
        "tools": "Celery 5.4 worker",
        "port": "internal",
        "category": "orchestration",
        "public_url": None,
        "checker": check_celery_worker,
    },
    {
        "id": "scheduler",
        "name": "scheduler",
        "tools": "Celery beat",
        "port": "internal",
        "category": "orchestration",
        "public_url": None,
        "checker": check_celery_scheduler,
    },
    {
        "id": "flower",
        "name": "flower",
        "tools": "Flower 2.0",
        "port": "5555",
        "category": "orchestration",
        "public_url": "http://localhost:5555",
        "checker": check_flower,
    },
    {
        "id": "openmetadata",
        "name": "openmetadata",
        "tools": "OpenMetadata 1.5.11",
        "port": "8585",
        "category": "catalog",
        "public_url": OPENMETADATA_PUBLIC_URL,
        "checker": check_openmetadata,
    },
    {
        "id": "prometheus",
        "name": "prometheus",
        "tools": "Prometheus",
        "port": "9090",
        "category": "observability",
        "public_url": PROMETHEUS_PUBLIC_URL,
        "checker": check_prometheus,
    },
    {
        "id": "grafana",
        "name": "grafana",
        "tools": "Grafana 13.2.3",
        "port": "3001",
        "category": "observability",
        "public_url": GRAFANA_PUBLIC_URL,
        "checker": check_grafana,
    },
    {
        "id": "python",
        "name": "python",
        "tools": "JupyterLab 4.3.3 · Python 3.11.16",
        "port": "8888",
        "category": "tooling",
        "public_url": "http://localhost:8888",
        "checker": check_jupyter,
    },
]


async def get_platform_report() -> Dict[str, Any]:
    """Probe every service concurrently and summarise the stack."""
    services = []
    for entry in SERVICE_CATALOG:
        services.append(
            asyncio.create_task(_probe(entry), name=f"probe-{entry['id']}")
        )

    results = await asyncio.gather(*services, return_exceptions=True)

    rows: List[Dict[str, Any]] = []
    for entry, result in zip(SERVICE_CATALOG, results):
        if isinstance(result, Exception):
            row = {
                "status": STATUS_DOWN,
                "detail": f"{type(result).__name__}: {result}"[:180],
                "latency_ms": None,
            }
        else:
            row = result
        rows.append(
            {
                "id": entry["id"],
                "name": entry["name"],
                "tools": entry["tools"],
                "port": entry["port"],
                "category": entry["category"],
                "category_label": CATEGORY_LABELS[entry["category"]],
                "public_url": entry["public_url"],
                **row,
            }
        )

    healthy = sum(1 for row in rows if row["status"] == STATUS_HEALTHY)
    degraded = sum(1 for row in rows if row["status"] == STATUS_DEGRADED)
    down = sum(1 for row in rows if row["status"] == STATUS_DOWN)

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "total": len(rows),
            "healthy": healthy,
            "degraded": degraded,
            "down": down,
            "availability_pct": round(
                (healthy + degraded * 0.5) / len(rows) * 100, 1
            )
            if rows
            else 0.0,
            "avg_latency_ms": round(
                sum(row["latency_ms"] for row in rows if row.get("latency_ms")) / healthy,
                1,
            )
            if healthy
            else None,
        },
        "categories": CATEGORY_LABELS,
        "services": rows,
    }


async def _probe(entry: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return await entry["checker"]()
    except Exception as exc:
        return {"status": STATUS_DOWN, "detail": f"{type(exc).__name__}: {exc}"[:180]}