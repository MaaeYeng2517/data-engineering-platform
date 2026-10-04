"""OpenMetadata API client."""
import logging
from typing import Any, Dict, List, Optional

import httpx

from backend.config import (
    OPENMETADATA_PASSWORD,
    OPENMETADATA_PUBLIC_URL,
    OPENMETADATA_URL,
    OPENMETADATA_USERNAME,
)

logger = logging.getLogger(__name__)

_token_cache: Optional[str] = None


async def _get_token() -> Optional[str]:
    global _token_cache
    if _token_cache:
        return _token_cache
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                f"{OPENMETADATA_URL.rstrip('/')}/api/v1/users/login",
                json={
                    "email": OPENMETADATA_USERNAME,
                    "password": OPENMETADATA_PASSWORD,
                },
            )
            response.raise_for_status()
            _token_cache = response.json().get("token")
            return _token_cache
    except httpx.HTTPError as exc:
        logger.warning("OpenMetadata login failed: %s", exc)
        return None


async def _request(method: str, path: str, **kwargs: Any) -> Optional[Any]:
    token = await _get_token()
    if not token:
        return None
    headers = {"Authorization": f"Bearer {token}"}
    url = f"{OPENMETADATA_URL.rstrip('/')}{path}"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            if not response.content:
                return None
            return response.json()
    except httpx.HTTPError as exc:
        logger.warning("OpenMetadata request failed: %s %s -> %s", method, path, exc)
        return None


async def get_version() -> Optional[Dict[str, Any]]:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OPENMETADATA_URL.rstrip('/')}/api/v1/system/version")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError:
        return None


async def get_health() -> Dict[str, Any]:
    version = await get_version()
    if version:
        return {"status": "healthy", "version": version.get("version")}
    return {"status": "unreachable"}


async def list_tables(limit: int = 50) -> List[Dict[str, Any]]:
    data = await _request("GET", "/api/v1/tables", params={"limit": limit})
    if not data:
        return []
    tables = []
    for item in data.get("data", []):
        tables.append(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "fully_qualified_name": item.get("fullyQualifiedName"),
                "table_type": item.get("tableType"),
                "schema": item.get("schema", {}).get("name") if isinstance(item.get("schema"), dict) else item.get("schema"),
                "database": item.get("database", {}).get("name") if isinstance(item.get("database"), dict) else item.get("database"),
                "description": (item.get("description") or "")[:500],
                "updated_at": item.get("updatedAt"),
                "url": f"{OPENMETADATA_PUBLIC_URL.rstrip('/')}/table/{item.get('fullyQualifiedName')}",
            }
        )
    return tables


async def search_catalog(query: str, limit: int = 20) -> List[Dict[str, Any]]:
    data = await _request(
        "GET",
        "/api/v1/search/query",
        params={"q": query, "limit": limit},
    )
    if not data:
        return []
    return [
        {
            "type": item.get("type"),
            "name": item.get("name") or item.get("suggestion"),
            "fully_qualified_name": item.get("fullyQualifiedName"),
            "description": (item.get("description") or "")[:300],
            "href": item.get("href"),
        }
        for item in data.get("data", [])
    ]


async def get_table_lineage(fully_qualified_name: str) -> Optional[Dict[str, Any]]:
    return await _request(
        "GET",
        f"/api/v1/lineage/table/{fully_qualified_name}",
        params={"upstreamDepth": 3, "downstreamDepth": 3},
    )


async def list_glossary_terms(limit: int = 50) -> List[Dict[str, Any]]:
    data = await _request("GET", "/api/v1/glossaryTerms", params={"limit": limit})
    if not data:
        return []
    return [
        {
            "name": item.get("name"),
            "fully_qualified_name": item.get("fullyQualifiedName"),
            "description": (item.get("description") or "")[:300],
        }
        for item in data.get("data", [])
    ]
