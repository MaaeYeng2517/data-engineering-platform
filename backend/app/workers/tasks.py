"""Celery tasks for ingestion, processing and indexing."""
import asyncio
import logging
import uuid
from typing import Any, Dict

from backend.app.services.chunking import token_chunker
from backend.app.services.embedding import embedding_service
from backend.app.services.indexing import hybrid_index
from backend.app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="dataair.index.document", bind=True, max_retries=3)
def index_document(self, doc_id: str, content: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Chunk a document and index every chunk in the hybrid index."""
    metadata = {**({"doc_id": str(doc_id)}), **(metadata or {})}
    chunks = token_chunker.chunk(content, metadata)

    chunk_ids = hybrid_index.vector_index.index_chunks(chunks)
    hybrid_index.keyword_index.index(str(doc_id), content, metadata)
    hybrid_index.metadata_index.index(str(doc_id), metadata)

    logger.info("Indexed document %s into %d chunks", doc_id, len(chunk_ids))
    return {"doc_id": str(doc_id), "chunk_count": len(chunk_ids), "chunk_ids": chunk_ids}


@celery_app.task(name="dataair.index.query", bind=True)
def search_index(self, query: str, limit: int = 10) -> Dict[str, Any]:
    """Run a hybrid search against the in-process index."""
    results = hybrid_index.search(query, limit=limit)
    return {"query": query, "results": results, "total": len(results)}


@celery_app.task(name="dataair.index.embed", bind=True)
def embed_texts(self, texts: list[str]) -> Dict[str, Any]:
    """Expose the embedding service to Celery callers."""
    vectors = embedding_service.embed(texts)
    return {"count": len(vectors), "vector_size": embedding_service.vector_size}


@celery_app.task(name="dataair.ingest.document", bind=True, max_retries=2)
def ingest_document(self, doc_id: str, content: str, metadata: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Ingest raw content then hand off to indexing."""
    return index_document.apply_async(kwargs={"doc_id": doc_id, "content": content, "metadata": metadata}).get()


def run_async(coro):
    """Run a coroutine from Celery's synchronous task context."""
    return asyncio.run(coro)


@celery_app.task(name="dataair.ingest.uuid")
def new_document_id() -> str:
    """Generate an identifier for a new document."""
    return str(uuid.uuid4())