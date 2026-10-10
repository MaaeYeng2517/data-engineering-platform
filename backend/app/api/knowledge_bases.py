"""Knowledge Bases API endpoints"""
import re
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_current_user
from backend.app.models.chunk import Chunk
from backend.app.models.document import Document
from backend.app.models.knowledge_base import KnowledgeBase
from backend.app.models.user import User
from backend.app.schemas import KnowledgeBaseCreate, KnowledgeBaseResponse
from backend.app.services.indexing import hybrid_index
from backend.database import get_db

router = APIRouter()

# Knowledge base lifecycle: draft while it is being filled, published once its
# documents are searchable, archived when it is retired but kept.
STATUS_DRAFT = "draft"
STATUS_PUBLISHED = "published"
STATUS_ARCHIVED = "archived"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "knowledge-base"


async def _get_scoped(db: AsyncSession, kb_id: UUID, user: User) -> KnowledgeBase:
    """Return the knowledge base only if it belongs to the caller's workspace."""
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.tenant_id == user.tenant_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return record


@router.post("/", response_model=KnowledgeBaseResponse)
async def create_kb(
    kb: KnowledgeBaseCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new knowledge base owned by the calling user."""
    slug = kb.slug or _slugify(kb.name)

    existing = await db.execute(
        select(func.count())
        .select_from(KnowledgeBase)
        .where(
            KnowledgeBase.tenant_id == user.tenant_id,
            KnowledgeBase.slug == slug,
        )
    )
    if existing.scalar_one():
        raise HTTPException(status_code=409, detail="A knowledge base with that slug already exists")

    record = KnowledgeBase(
        tenant_id=user.tenant_id,
        owner_id=user.id,
        name=kb.name,
        description=kb.description,
        slug=slug,
        settings=kb.settings or {},
        status=STATUS_DRAFT,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/", response_model=List[KnowledgeBaseResponse])
async def list_kbs(
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the knowledge bases visible to the caller's workspace."""
    query = select(KnowledgeBase).where(KnowledgeBase.tenant_id == user.tenant_id)
    if status:
        query = query.where(KnowledgeBase.status == status)

    result = await db.execute(query.order_by(KnowledgeBase.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_kb(
    kb_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get knowledge base by ID"""
    return await _get_scoped(db, kb_id, user)


@router.get("/{kb_id}/stats")
async def kb_stats(
    kb_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Document and chunk counts for a knowledge base."""
    await _get_scoped(db, kb_id, user)

    documents = await db.execute(
        select(func.count()).select_from(Document).where(Document.kb_id == kb_id)
    )
    chunks = await db.execute(
        select(func.count()).select_from(Chunk).where(Chunk.kb_id == kb_id)
    )

    return {
        "kb_id": str(kb_id),
        "documents": documents.scalar_one(),
        "chunks": chunks.scalar_one(),
        "indexed_chunks": hybrid_index.chunk_count([str(kb_id)]),
    }


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_kb(
    kb_id: UUID,
    kb: KnowledgeBaseCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update knowledge base"""
    record = await _get_scoped(db, kb_id, user)

    record.name = kb.name
    record.description = kb.description
    if kb.slug:
        record.slug = kb.slug
    record.settings = kb.settings or {}

    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{kb_id}")
async def delete_kb(
    kb_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a knowledge base with its documents, chunks and index entries."""
    record = await _get_scoped(db, kb_id, user)

    document_ids = list(
        (
            await db.execute(select(Document.id).where(Document.kb_id == record.id))
        ).scalars().all()
    )
    for document_id in document_ids:
        hybrid_index.delete_document(str(document_id))

    await db.delete(record)
    await db.commit()
    return {"message": "Knowledge base deleted"}


@router.post("/{kb_id}/publish")
async def publish_kb(
    kb_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Publish a knowledge base once it has at least one indexed document."""
    record = await _get_scoped(db, kb_id, user)

    indexed = await db.execute(
        select(func.count()).select_from(Document).where(Document.kb_id == record.id)
    )
    if not indexed.scalar_one():
        raise HTTPException(
            status_code=409,
            detail="Add at least one document before publishing this knowledge base",
        )

    record.is_published = True
    record.status = STATUS_PUBLISHED

    await db.commit()
    return {"message": "Knowledge base published", "kb_id": str(kb_id)}


@router.post("/{kb_id}/archive")
async def archive_kb(
    kb_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retire a knowledge base without deleting it."""
    record = await _get_scoped(db, kb_id, user)

    record.is_published = False
    record.status = STATUS_ARCHIVED

    await db.commit()
    return {"message": "Knowledge base archived", "kb_id": str(kb_id)}