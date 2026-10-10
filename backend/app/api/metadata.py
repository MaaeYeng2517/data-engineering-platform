"""Metadata API endpoints"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_current_user
from backend.app.models.knowledge_base import KnowledgeBase
from backend.app.models.metadata import MetadataSchema
from backend.app.models.user import User
from backend.app.schemas import MetadataSchemaCreate, MetadataSchemaResponse
from backend.database import get_db

router = APIRouter()


async def _get_scoped(db: AsyncSession, schema_id: UUID, user: User) -> MetadataSchema:
    """Return the schema only if its knowledge base is in the caller's workspace."""
    result = await db.execute(
        select(MetadataSchema)
        .join(KnowledgeBase, KnowledgeBase.id == MetadataSchema.kb_id)
        .where(MetadataSchema.id == schema_id, KnowledgeBase.tenant_id == user.tenant_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Schema not found")
    return record


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


@router.post("/", response_model=MetadataSchemaResponse)
async def create_schema(
    schema: MetadataSchemaCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a metadata schema"""
    kb = await _require_kb(db, schema.kb_id, user)

    record = MetadataSchema(
        kb_id=kb.id,
        name=schema.name,
        description=schema.description,
        fields=schema.fields,
        taxonomy=schema.taxonomy or {},
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/", response_model=List[MetadataSchemaResponse])
async def list_schemas(
    kb_id: Optional[UUID] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List metadata schemas in the caller's workspace"""
    query = (
        select(MetadataSchema)
        .join(KnowledgeBase, KnowledgeBase.id == MetadataSchema.kb_id)
        .where(KnowledgeBase.tenant_id == user.tenant_id)
    )
    if kb_id is not None:
        query = query.where(MetadataSchema.kb_id == kb_id)

    result = await db.execute(query.order_by(MetadataSchema.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{schema_id}", response_model=MetadataSchemaResponse)
async def get_schema(
    schema_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get schema by ID"""
    return await _get_scoped(db, schema_id, user)


@router.put("/{schema_id}", response_model=MetadataSchemaResponse)
async def update_schema(
    schema_id: UUID,
    schema: MetadataSchemaCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update schema"""
    record = await _get_scoped(db, schema_id, user)

    record.name = schema.name
    record.description = schema.description
    record.fields = schema.fields
    record.taxonomy = schema.taxonomy or {}

    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{schema_id}")
async def delete_schema(
    schema_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete schema"""
    record = await _get_scoped(db, schema_id, user)

    await db.delete(record)
    await db.commit()
    return {"message": "Schema deleted"}


@router.post("/{schema_id}/validate")
async def validate_data(
    schema_id: UUID,
    data: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Validate a payload against a stored metadata schema."""
    from backend.app.services.metadata import metadata_engine

    record = await _get_scoped(db, schema_id, user)
    return metadata_engine.validate_fields(record.fields or [], data)