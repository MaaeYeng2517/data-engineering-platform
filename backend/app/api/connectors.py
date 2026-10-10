"""Connectors & Data Sources API endpoints"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_current_user, require_platform_user
from backend.app.models.knowledge_base import KnowledgeBase
from backend.app.models.source import Source
from backend.app.models.user import User
from backend.app.utils.time import utcnow
from backend.database import get_db

# Public router for endpoints that don't require authentication
public_router = APIRouter()

# Protected router for endpoints that require authentication
router = APIRouter(dependencies=[Depends(require_platform_user)])


class SourceCreate(BaseModel):
    kb_id: UUID
    name: str
    source_type: str
    config: dict


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    config: Optional[dict] = None
    is_active: Optional[bool] = None


class TestConnectionRequest(BaseModel):
    source_type: str
    config: dict


class SyncLegacyRequest(BaseModel):
    source_type: str
    config: dict
    source_id: Optional[str] = None


class SourceResponse(BaseModel):
    id: str
    kb_id: str
    name: str
    source_type: str
    config: dict
    is_active: bool
    last_sync: Optional[str]
    sync_status: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


async def _require_kb(db: AsyncSession, kb_id: UUID, user: User) -> KnowledgeBase:
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.tenant_id == user.tenant_id,
        )
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


async def _get_source(db: AsyncSession, source_id: UUID, user: User) -> Source:
    result = await db.execute(
        select(Source)
        .join(KnowledgeBase, KnowledgeBase.id == Source.kb_id)
        .where(Source.id == source_id, KnowledgeBase.tenant_id == user.tenant_id)
    )
    source = result.scalar_one_or_none()
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.post("/sources", response_model=SourceResponse, status_code=201)
async def create_source(
    payload: SourceCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a data source"""
    await _require_kb(db, payload.kb_id, user)

    source = Source(
        kb_id=payload.kb_id,
        name=payload.name,
        source_type=payload.source_type,
        config=payload.config,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)

    return SourceResponse(
        id=str(source.id),
        kb_id=str(source.kb_id),
        name=source.name,
        source_type=source.source_type,
        config=source.config,
        is_active=source.is_active,
        last_sync=source.last_sync.isoformat() if source.last_sync else None,
        sync_status=source.sync_status,
        created_at=source.created_at.isoformat() if source.created_at else None,
        updated_at=source.updated_at.isoformat() if source.updated_at else None,
    )


@router.get("/sources", response_model=List[SourceResponse])
async def list_sources(
    kb_id: Optional[UUID] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List data sources in the workspace"""
    query = (
        select(Source)
        .join(KnowledgeBase, KnowledgeBase.id == Source.kb_id)
        .where(KnowledgeBase.tenant_id == user.tenant_id)
    )
    if kb_id:
        query = query.where(Source.kb_id == kb_id)

    result = await db.execute(query.order_by(Source.created_at.desc()))
    sources = result.scalars().all()
    return [
        SourceResponse(
            id=str(s.id),
            kb_id=str(s.kb_id),
            name=s.name,
            source_type=s.source_type,
            config=s.config,
            is_active=s.is_active,
            last_sync=s.last_sync.isoformat() if s.last_sync else None,
            sync_status=s.sync_status,
            created_at=s.created_at.isoformat() if s.created_at else None,
            updated_at=s.updated_at.isoformat() if s.updated_at else None,
        )
        for s in sources
    ]


@router.get("/sources/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a data source by ID"""
    source = await _get_source(db, source_id, user)
    return SourceResponse(
        id=str(source.id),
        kb_id=str(source.kb_id),
        name=source.name,
        source_type=source.source_type,
        config=source.config,
        is_active=source.is_active,
        last_sync=source.last_sync.isoformat() if source.last_sync else None,
        sync_status=source.sync_status,
        created_at=source.created_at.isoformat() if source.created_at else None,
        updated_at=source.updated_at.isoformat() if source.updated_at else None,
    )


@router.patch("/sources/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: UUID,
    payload: SourceUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a data source"""
    source = await _get_source(db, source_id, user)
    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)
    return SourceResponse(
        id=str(source.id),
        kb_id=str(source.kb_id),
        name=source.name,
        source_type=source.source_type,
        config=source.config,
        is_active=source.is_active,
        last_sync=source.last_sync.isoformat() if source.last_sync else None,
        sync_status=source.sync_status,
        created_at=source.created_at.isoformat() if source.created_at else None,
        updated_at=source.updated_at.isoformat() if source.updated_at else None,
    )


@router.delete("/sources/{source_id}")
async def delete_source(
    source_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a data source"""
    source = await _get_source(db, source_id, user)
    await db.delete(source)
    await db.commit()
    return {"message": "Source deleted"}


@router.post("/sources/{source_id}/sync")
async def sync_source(
    source_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger a sync for a data source"""
    from backend.app.services.connectors import connector_manager

    source = await _get_source(db, source_id, user)

    try:
        connector = connector_manager.get_connector(source.source_type, source.config)
        source.sync_status = "running"
        await db.commit()

        test_result = await connector.test_connection()
        if test_result.get("status") != "ok":
            source.sync_status = "failed"
            await db.commit()
            raise HTTPException(status_code=400, detail="Connection test failed")

        result = await connector.sync(source.name, incremental=True)
        source.sync_status = "success"
        source.last_sync = utcnow()
        await db.commit()

        return {
            "source_id": str(source_id),
            "status": "success",
            "result": result,
            "synced_at": source.last_sync.isoformat() if source.last_sync else None,
        }
    except HTTPException:
        raise
    except Exception as e:
        source.sync_status = "failed"
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))


@public_router.get("/types")
async def get_connector_types():
    """Get supported connector types"""
    from backend.app.services.connectors import connector_manager

    return {
        "types": connector_manager.list_supported_types()
    }


@public_router.post("/test")
async def test_connection(payload: TestConnectionRequest):
    """Test a connector connection"""
    from backend.app.services.connectors import connector_manager

    try:
        connector = connector_manager.get_connector(payload.source_type, payload.config)
        result = await connector.test_connection()

        return {
            "source_type": payload.source_type,
            "status": "success",
            "result": result
        }
    except Exception as e:
        return {
            "source_type": payload.source_type,
            "status": "error",
            "error": str(e)
        }


@router.post("/sync")
async def sync_source_legacy(payload: SyncLegacyRequest):
    """Sync from a source (legacy endpoint)"""
    from backend.app.services.connectors import connector_manager

    try:
        connector = connector_manager.get_connector(payload.source_type, payload.config)

        test_result = await connector.test_connection()
        if test_result.get("status") != "ok":
            raise HTTPException(status_code=400, detail="Connection test failed")

        result = await connector.sync(payload.source_id or "default", incremental=True)

        return {
            "source_type": payload.source_type,
            "status": "success",
            "result": result,
            "synced_at": utcnow().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources-legacy")
async def list_sources_legacy(source_type: str = None):
    """List available sources (legacy endpoint)"""
    from backend.app.services.connectors import connector_manager

    if source_type:
        connector = connector_manager.get_connector(source_type, {})
        sources = await connector.list_sources()
    else:
        sources = []
        for st in connector_manager.list_supported_types():
            connector = connector_manager.get_connector(st, {})
            sources.extend(await connector.list_sources())

    return {
        "sources": sources
    }