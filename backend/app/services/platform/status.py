"""Aggregated platform/system status."""
import asyncio
from typing import Any, Dict

from backend.app.services.platform import airflow, minio_storage, openmetadata, prometheus
from backend.database import async_session_factory
from sqlalchemy import text


async def _postgres_status() -> Dict[str, Any]:
    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as exc:
        return {"status": "unhealthy", "error": str(exc)}


async def _redis_status() -> Dict[str, Any]:
    from backend.config import REDIS_URL

    try:
        import redis.asyncio as aioredis

        client = aioredis.from_url(REDIS_URL, socket_timeout=5)
        await client.ping()
        await client.aclose()
        return {"status": "healthy"}
    except Exception as exc:
        return {"status": "unreachable", "error": str(exc)}


async def get_system_status() -> Dict[str, Any]:
    postgres, redis, minio, airflow_health, om, prom = await asyncio.gather(
        _postgres_status(),
        _redis_status(),
        minio_storage.get_health(),
        airflow.get_health(),
        openmetadata.get_health(),
        prometheus.get_health(),
    )
    systems = {
        "postgres": postgres,
        "redis": redis,
        "minio": minio,
        "airflow": airflow_health,
        "openmetadata": om,
        "prometheus": prom,
    }
    healthy = sum(
        1 for info in systems.values() if info.get("status") in {"healthy", "degraded"}
    )
    return {
        "systems": systems,
        "summary": {
            "total": len(systems),
            "healthy": healthy,
            "unhealthy": len(systems) - healthy,
        },
    }
