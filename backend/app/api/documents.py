"""Documents API endpoints."""
import hashlib
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_current_user
from backend.app.models.chunk import Chunk
from backend.app.models.document import Document
from backend.app.models.knowledge_base import KnowledgeBase
from backend.app.models.user import User
from backend.app.schemas import DocumentCreate, DocumentResponse
from backend.app.services.indexing.pipeline import remove_document
from backend.app.workers.tasks import index_document_task
from backend.database import get_db

router = APIRouter()

# Text extracted from an upload is stored on the document, but only these
# characters are worth keeping per record; the chunks hold the rest.
MAX_INLINE_CHARS = 2_000_000


async def _get_scoped(db: AsyncSession, doc_id: UUID, user: User) -> Document:
    """Return the document only if it belongs to the caller's workspace."""
    result = await db.execute(
        select(Document)
        .join(KnowledgeBase, KnowledgeBase.id == Document.kb_id)
        .where(Document.id == doc_id, KnowledgeBase.tenant_id == user.tenant_id)
    )
    document = result.scalar_one_or_none()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


async def _resolve_kb(db: AsyncSession, kb_id: UUID, user: User) -> KnowledgeBase:
    """Load a knowledge base the caller is allowed to write to."""
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


@router.post("/", response_model=DocumentResponse)
async def create_document(
    doc: DocumentCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a document from inline content and index it for search."""
    kb = await _resolve_kb(db, doc.kb_id, user)

    document = Document(
        kb_id=kb.id,
        title=doc.title,
        source_type=doc.source_type,
        source_url=doc.source_url,
        content=doc.content,
        data=doc.metadata,
        status="pending",
    )
    db.add(document)
    await db.flush()

    index_document_task.delay(str(document.id), content=document.content)
    document.status = "queued"

    await db.commit()
    await db.refresh(document)
    return document


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    kb_id: str = Form(...),
    title: str = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document file into a knowledge base and index it.

    ``kb_id`` and ``title`` are read as form fields because multipart uploads
    cannot carry a JSON body; a query parameter would be silently ignored.
    """
    try:
        parsed_kb_id = UUID(kb_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="kb_id must be a UUID") from exc

    kb = await _resolve_kb(db, parsed_kb_id, user)

    content = await file.read()
    text = content.decode("utf-8", errors="ignore")

    document = Document(
        kb_id=kb.id,
        title=title or file.filename or "Untitled",
        source_type="file",
        file_size=len(content),
        mime_type=file.content_type,
        checksum=hashlib.sha256(content).hexdigest(),
        content=text[:MAX_INLINE_CHARS],
        status="processing",
    )
    db.add(document)
    await db.flush()

    index_document_task.delay(str(document.id), content=document.content)
    document.status = "queued"

    await db.commit()
    await db.refresh(document)
    return document


@router.get("/", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: Optional[UUID] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List documents in the caller's workspace, optionally by knowledge base."""
    query = (
        select(Document)
        .join(KnowledgeBase, KnowledgeBase.id == Document.kb_id)
        .where(KnowledgeBase.tenant_id == user.tenant_id)
        .order_by(Document.created_at.desc())
    )
    if kb_id is not None:
        query = query.where(Document.kb_id == kb_id)

    result = await db.execute(query)
    return list(result.scalars().all())


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get document by ID"""
    return await _get_scoped(db, doc_id, user)


@router.get("/{doc_id}/chunks")
async def list_document_chunks(
    doc_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List the chunks a document was split into."""
    await _get_scoped(db, doc_id, user)

    result = await db.execute(
        select(Chunk)
        .where(Chunk.document_id == doc_id)
        .order_by(Chunk.chunk_index)
    )
    return [
        {
            "id": str(chunk.id),
            "document_id": str(chunk.document_id),
            "chunk_index": chunk.chunk_index,
            "token_count": chunk.token_count,
            "content": chunk.content,
        }
        for chunk in result.scalars().all()
    ]


@router.post("/{doc_id}/reindex", response_model=DocumentResponse)
async def reindex_document(
    doc_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Re-chunk and re-embed a document from its stored content."""
    document = await _get_scoped(db, doc_id, user)

    document.status = "processing"
    index_document_task.delay(str(document.id), content=document.content)
    document.status = "queued"

    await db.commit()
    await db.refresh(document)
    return document


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document, its chunks and its index entries."""
    document = await _get_scoped(db, doc_id, user)

    await remove_document(db, document.id)
    await db.delete(document)
    await db.commit()

    return {"message": "Document deleted"}