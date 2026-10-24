"""Visualization API - Apache Superset integration."""
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

from backend.app.services.platform import superset

router = APIRouter()


@router.get("/health")
async def superset_health():
    return await superset.get_health()


@router.get("/dashboards")
async def superset_dashboards(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return await superset.list_dashboards(limit=limit, offset=offset)


@router.get("/dashboards/{dashboard_id}")
async def superset_dashboard(dashboard_id: int):
    dashboard = await superset.get_dashboard(dashboard_id)
    if not dashboard:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return dashboard


@router.get("/dashboards/{dashboard_id}/embed")
async def superset_dashboard_embed(dashboard_id: int):
    embed = await superset.get_dashboard_embed(dashboard_id)
    if not embed:
        raise HTTPException(status_code=404, detail="Embed info not found")
    return embed


@router.post("/dashboards/{dashboard_id}/guest-token")
async def superset_guest_token(dashboard_id: int, body: Optional[Dict[str, Any]] = None):
    body = body or {}
    token = await superset.create_guest_token(
        dashboard_id,
        user=body.get("user"),
        resources=body.get("resources"),
        rls=body.get("rls"),
    )
    if not token:
        raise HTTPException(status_code=502, detail="Failed to create guest token")
    return token
