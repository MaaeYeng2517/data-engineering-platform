"""Airflow REST API client."""
import base64
import logging
from typing import Any, Dict, List, Optional

import httpx

from backend.config import AIRFLOW_PASSWORD, AIRFLOW_PUBLIC_URL, AIRFLOW_URL, AIRFLOW_USERNAME

logger = logging.getLogger(__name__)


def _basic_auth() -> str:
    token = base64.b64encode(
        f"{AIRFLOW_USERNAME}:{AIRFLOW_PASSWORD}".encode()
    ).decode()
    return f"Basic {token}"


async def _request(method: str, path: str, **kwargs: Any) -> Optional[Dict]:
    url = f"{AIRFLOW_URL.rstrip('/')}{path}"
    headers = {"Authorization": _basic_auth(), "Accept": "application/json"}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return None
            return response.json()
    except httpx.HTTPError as exc:
        logger.warning("Airflow request failed: %s %s -> %s", method, path, exc)
        return None


async def get_health() -> Dict[str, Any]:
    url = f"{AIRFLOW_URL.rstrip('/')}/health"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return {"status": "unhealthy", "http_status": response.status_code}
            data = response.json()
            components = {
                "scheduler": (data.get("scheduler") or {}).get("status"),
                "database": (data.get("metadatabase") or data.get("database") or {}).get("status"),
                "triggerer": (data.get("triggerer") or {}).get("status"),
            }
            healthy = all(v == "healthy" for v in components.values())
            return {"status": "healthy" if healthy else "degraded", **components}
    except httpx.HTTPError as exc:
        return {"status": "unreachable", "error": str(exc)}


async def list_dags(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    data = await _request(
        "GET",
        "/api/v1/dags",
        params={"limit": limit, "offset": offset, "only_active": "true"},
    )
    if not data:
        return []
    dags = []
    for item in data.get("dags", []):
        schedule = item.get("schedule_interval") or {}
        dags.append(
            {
                "dag_id": item.get("dag_id"),
                "description": item.get("description"),
                "is_paused": item.get("is_paused"),
                "is_active": item.get("is_active"),
                "schedule": schedule.get("value") if isinstance(schedule, dict) else schedule,
                "tags": [tag.get("name") for tag in item.get("tags", [])],
                "file_path": item.get("fileloc"),
                "next_run": item.get("next_dagrun"),
                "url": f"{AIRFLOW_PUBLIC_URL.rstrip('/')}/dags/{item.get('dag_id')}/grid",
            }
        )
    return dags


async def get_dag(dag_id: str) -> Optional[Dict[str, Any]]:
    return await _request("GET", f"/api/v1/dags/{dag_id}")


async def list_dag_runs(dag_id: str, limit: int = 25) -> List[Dict[str, Any]]:
    data = await _request(
        "GET",
        f"/api/v1/dags/{dag_id}/dagRuns",
        params={"limit": limit},
    )
    if not data:
        return []
    return [
        {
            "run_id": run.get("dag_run_id"),
            "state": run.get("state"),
            "execution_date": run.get("execution_date"),
            "start_date": run.get("start_date"),
            "end_date": run.get("end_date"),
            "conf": run.get("conf"),
        }
        for run in data.get("dag_runs", [])
    ]


async def get_dag_run_task_instances(dag_id: str, run_id: str) -> List[Dict[str, Any]]:
    data = await _request(
        "GET",
        f"/api/v1/dags/{dag_id}/dagRuns/{run_id}/taskInstances",
    )
    if not data:
        return []
    return [
        {
            "task_id": ti.get("task_id"),
            "state": ti.get("state"),
            "try_number": ti.get("try_number"),
            "start_date": ti.get("start_date"),
            "end_date": ti.get("end_date"),
            "duration": ti.get("duration"),
            "operator": ti.get("task_type"),
        }
        for ti in data
    ]


async def trigger_dag(dag_id: str, conf: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    payload = {"dag_run_id": f"manual__{int(__import__('time').time())}"}
    if conf:
        payload["conf"] = conf
    return await _request(
        "POST",
        f"/api/v1/dags/{dag_id}/dagRuns",
        json=payload,
    )


async def set_dag_pause(dag_id: str, paused: bool) -> Optional[Dict[str, Any]]:
    return await _request(
        "PATCH",
        f"/api/v1/dags/{dag_id}",
        json={"is_paused": paused},
    )
