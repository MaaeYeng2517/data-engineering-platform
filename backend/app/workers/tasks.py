"""Celery tasks for ingestion, processing and indexing.

Postgres is the source of truth for chunks; the search index is a per-process
copy that the API rebuilds on startup. So a task here persists chunks and
rebuilds the *worker's* copy — anything the API serves comes from its own index,
which it rehydrates from the same rows.
"""
import asyncio
import logging
import uuid
from typing import Any, Dict
from uuid import UUID

from sqlalchemy import select

from backend.app.models.document import Document
from backend.app.services.embedding import embedding_service
from backend.app.services.indexing import hybrid_index
from backend.app.services.indexing.pipeline import index_document, rehydrate_index
from backend.app.workers.celery_app import celery_app
from backend.database import async_session_factory

logger = logging.getLogger(__name__)


def _maybe_task(func):
    """Apply the celery decorator when celery is available; otherwise return the function unchanged."""
    if celery_app is not None:
        return celery_app.task(name=func.__name__.replace("_", "."), bind=True)(func)
    return func


def run_async(coro):
    """Run a coroutine from Celery's synchronous task context."""
    return asyncio.run(coro)


async def _index_stored_document(document_id: UUID, content: str | None) -> Dict[str, Any]:
    """Persist chunks for a stored document and index them in this process."""
    async with async_session_factory() as db:
        document = (
            await db.execute(select(Document).where(Document.id == document_id))
        ).scalar_one_or_none()
        if document is None:
            return {"doc_id": str(document_id), "chunk_count": 0, "chunk_ids": []}

        chunk_ids = await index_document(db, document, content=content)
        document.status = "processed"
        await db.commit()
        return {"doc_id": str(document_id), "chunk_count": len(chunk_ids), "chunk_ids": chunk_ids}


async def _rehydrate() -> int:
    """Rebuild this process's index from the stored chunks."""
    async with async_session_factory() as db:
        return await rehydrate_index(db)


@_maybe_task
def index_document_task(
    self_,
    doc_id: str,
    content: str | None = None,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Chunk, embed and index a stored document."""
    try:
        document_id = UUID(str(doc_id))
    except ValueError as exc:
        raise ValueError(f"doc_id must be a UUID, got {doc_id!r}") from exc

    result = run_async(_index_stored_document(document_id, content))
    logger.info("Indexed document %s into %d chunks", doc_id, result["chunk_count"])
    return result


@_maybe_task
def search_index(
    self_,
    query: str,
    limit: int = 10,
) -> Dict[str, Any]:
    """Run a hybrid search against this process's index, hydrating it first."""
    if len(hybrid_index) == 0:
        run_async(_rehydrate())

    results = hybrid_index.search(query, limit=limit)
    return {"query": query, "results": results, "total": len(results)}


@_maybe_task
def embed_texts(
    self_,
    texts: list[str],
) -> Dict[str, Any]:
    """Expose the embedding service to Celery callers."""
    vectors = embedding_service.embed(texts)
    return {"count": len(vectors), "vector_size": embedding_service.vector_size}


@_maybe_task
def ingest_document(
    self_,
    doc_id: str,
    content: str | None = None,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Ingest raw content then hand off to indexing."""
    if celery_app is not None:
        result = index_document_task.apply_async(
            kwargs={"doc_id": doc_id, "content": content, "metadata": metadata}
        ).get()
    else:
        result = index_document_task(
            doc_id, content=content, metadata=metadata
        )
    return result


@_maybe_task
def new_document_id(
    self_,
) -> str:
    """Generate an identifier for a new document."""
    return str(uuid.uuid4())