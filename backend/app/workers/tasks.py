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
        await db.commit()
        return {"doc_id": str(document_id), "chunk_count": len(chunk_ids), "chunk_ids": chunk_ids}


async def _rehydrate() -> int:
    """Rebuild this process's index from the stored chunks."""
    async with async_session_factory() as db:
        return await rehydrate_index(db)


@celery_app.task(name="dataair.index.document", bind=True, max_retries=3)
def index_document_task(
    self,
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


@celery_app.task(name="dataair.index.query", bind=True)
def search_index(self, query: str, limit: int = 10) -> Dict[str, Any]:
    """Run a hybrid search against this process's index, hydrating it first."""
    if len(hybrid_index) == 0:
        run_async(_rehydrate())

    results = hybrid_index.search(query, limit=limit)
    return {"query": query, "results": results, "total": len(results)}


@celery_app.task(name="dataair.index.embed", bind=True)
def embed_texts(self, texts: list[str]) -> Dict[str, Any]:
    """Expose the embedding service to Celery callers."""
    vectors = embedding_service.embed(texts)
    return {"count": len(vectors), "vector_size": embedding_service.vector_size}


@celery_app.task(name="dataair.ingest.document", bind=True, max_retries=2)
def ingest_document(
    self,
    doc_id: str,
    content: str | None = None,
    metadata: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Ingest raw content then hand off to indexing."""
    return index_document_task.apply_async(
        kwargs={"doc_id": doc_id, "content": content, "metadata": metadata}
    ).get()


@celery_app.task(name="dataair.ingest.uuid")
def new_document_id() -> str:
    """Generate an identifier for a new document."""
    return str(uuid.uuid4())