"""Apache Superset REST API client."""
import logging
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from backend.config import SUPERSET_PASSWORD, SUPERSET_PUBLIC_URL, SUPERSET_URL, SUPERSET_USERNAME

logger = logging.getLogger(__name__)

_access_token: Optional[str] = None


async def _get_access_token() -> Optional[str]:
    global _access_token
    if _access_token:
        return _access_token

    login_url = f"{SUPERSET_URL.rstrip('/')}/api/v1/security/login"
    payload = {
        "username": SUPERSET_USERNAME,
        "password": SUPERSET_PASSWORD,
        "provider": "db",
        "refresh": True,
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(login_url, json=payload)
            response.raise_for_status()
            data = response.json()
            _access_token = data.get("access_token") or data.get("token")
            return _access_token
    except httpx.HTTPError as exc:
        logger.warning("Superset login failed: %s", exc)
        _access_token = None
        return None


async def _request(
    method: str,
    path: str,
    *,
    auth: bool = True,
    **kwargs: Any,
) -> Optional[Dict]:
    url = f"{SUPERSET_URL.rstrip('/')}{path}"
    headers = {"Accept": "application/json"}
    if auth:
        token = await _get_access_token()
        if not token:
            return None
        headers["Authorization"] = f"Bearer {token}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            if response.status_code == 204 or not response.content:
                return None
            return response.json()
    except httpx.HTTPError as exc:
        logger.warning("Superset request failed: %s %s -> %s", method, path, exc)
        return None


async def get_health() -> Dict[str, Any]:
    # Try to hit health endpoint or just return status based on auth
    data = await _request("GET", "/health", auth=False)
    if data is not None:
        return {"status": "healthy", "raw": data}
    token = await _get_access_token()
    if token:
        return {"status": "healthy"}
    return {"status": "unreachable"}


async def list_dashboards(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
    data = await _request(
        "GET",
        "/api/v1/dashboard/",
        params={"q": f"(page_size:{limit};page:{offset // limit + 1})"},
    )
    if not data:
        # Try simpler params
        data = await _request(
            "GET",
            "/api/v1/dashboard/",
            params={"page_size": limit, "page": offset // limit + 1},
        )
    if not data:
        return []
    dashboards = []
    for item in data.get("result", []) or data.get("dashboards", []):
        dashboard_id = item.get("id")
        slug = item.get("slug") or ""
        dashboards.append(
            {
                "id": dashboard_id,
                "title": item.get("dashboard_title") or item.get("title"),
                "slug": slug,
                "url": f"{SUPERSET_PUBLIC_URL.rstrip('/')}/superset/dashboard/{slug or dashboard_id}/",
                "published": item.get("published"),
                "changed_on_utc": item.get("changed_on_utc") or item.get("changed_on"),
                "tags": item.get("tags", []),
                "owners": [
                    owner.get("username") or owner.get("first_name")
                    for owner in item.get("owners", []) or []
                ],
            }
        )
    return dashboards


async def get_dashboard(dashboard_id: int) -> Optional[Dict[str, Any]]:
    return await _request("GET", f"/api/v1/dashboard/{dashboard_id}")


async def get_dashboard_embed(dashboard_id: int) -> Optional[Dict[str, Any]]:
    """Get embedded guest token info if available."""
    # Try common endpoints for embedding
    data = await _request("POST", f"/api/v1/dashboard/{dashboard_id}/embedded")
    if data:
        return data
    # Alternative approach - get dashboard and construct URL
    dashboard = await get_dashboard(dashboard_id)
    if dashboard:
        result = dashboard.get("result") or dashboard
        slug = result.get("slug") or dashboard_id
        return {
            "dashboard_id": dashboard_id,
            "embed_url": f"{SUPERSET_PUBLIC_URL.rstrip('/')}/superset/dashboard/{slug}/?standalone=true",
            "url": f"{SUPERSET_PUBLIC_URL.rstrip('/')}/superset/dashboard/{slug}/",
        }
    return None


async def create_guest_token(
    dashboard_id: int,
    user: Optional[Dict[str, Any]] = None,
    resources: Optional[List[Dict[str, Any]]] = None,
    rls: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    if resources is None:
        resources = [{"type": "dashboard", "id": dashboard_id}]
    payload: Dict[str, Any] = {
        "user": user or {"username": "guest", "first_name": "Guest", "last_name": "User"},
        "resources": resources,
        "rls": rls or [],
    }
    return await _request("POST", "/api/v1/security/guest_token/", json=payload)
