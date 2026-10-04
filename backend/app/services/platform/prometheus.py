"""Prometheus metrics client."""
import logging
from typing import Any, Dict, List, Optional

import httpx

from backend.config import PROMETHEUS_URL

logger = logging.getLogger(__name__)


async def _query(path: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    url = f"{PROMETHEUS_URL.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as exc:
        logger.warning("Prometheus query failed: %s -> %s", path, exc)
        return None


async def get_health() -> Dict[str, Any]:
    data = await _query("/api/v1/query", {"query": "up"})
    if data and data.get("status") == "success":
        targets = data.get("data", {}).get("result", [])
        up = sum(1 for t in targets if t.get("value", [None, "0"])[1] == "1")
        return {
            "status": "healthy" if up else "degraded",
            "targets_total": len(targets),
            "targets_up": up,
        }
    return {"status": "unreachable"}


async def instant_query(query: str) -> List[Dict[str, Any]]:
    data = await _query("/api/v1/query", {"query": query})
    if not data or data.get("status") != "success":
        return []
    return [
        {
            "metric": item.get("metric", {}),
            "value": item.get("value", []),
        }
        for item in data.get("data", {}).get("result", [])
    ]


async def range_query(query: str, hours: float = 24.0, step: str = "1h") -> List[Dict[str, Any]]:
    import time

    end = time.time()
    start = end - hours * 3600
    data = await _query(
        "/api/v1/query_range",
        {"query": query, "start": start, "end": end, "step": step},
    )
    if not data or data.get("status") != "success":
        return []
    return [
        {
            "metric": item.get("metric", {}),
            "values": item.get("values", []),
        }
        for item in data.get("data", {}).get("result", [])
    ]


async def get_platform_summary() -> Dict[str, Any]:
    queries = {
        "targets_up": "sum(up)",
        "targets_total": "count(up)",
        "http_requests_total": "sum(rate(http_requests_total[5m]))",
        "backend_up": "up{job=~'backend.*'}",
    }
    summary: Dict[str, Any] = {}
    for key, query in queries.items():
        results = await instant_query(query)
        summary[key] = results
    return summary
