"""Document → chunks → embeddings → index.

One implementation, used by the upload endpoint and by the Celery task, so a
document indexed either way lands in the same place with the same ids.

Chunk ids are the database UUIDs of the persisted ``Chunk`` rows. That keeps the
API's ``chunk_id`` a real identifier, and lets ``rehydrate_index()`` rebuild the
index from Postgres after a restart without recomputing embeddings.
"""
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.chunk import Chunk
from backend.app.models.document import Document
from backend.app.services.chunking import TokenChunker
from backend.app.services.embedding import embedding_service
from backend.app.services.indexing import build_entry, hybrid_index

logger = logging.getLogger(__name__)

# Words per chunk, and how much consecutive chunks overlap. Overlap keeps a
# sentence that straddles a boundary retrievable from either side.
CHUNK_TOKENS = 300
CHUNK_OVERLAP = 50

chunker = TokenChunker(CHUNK_TOKENS, CHUNK_OVERLAP)


def _document_metadata(document: Document) -> Dict[str, Any]:
    """Metadata every chunk of a document inherits."""
    return {
        "document_id": str(document.id),
        "kb_id": str(document.kb_id),
        "title": document.title,
        "source_type": document.source_type,
        "checksum": document.checksum,
    }


async def index_document(
    db: AsyncSession,
    document: Document,
    content: Optional[str] = None,
) -> List[str]:
    """Chunk, embed and index a document, replacing any previous chunks.

    Returns the chunk ids that ended up in the index. The caller owns the
    transaction: this flushes but never commits.
    """
    text = content if content is not None else (document.content or "")
    document_id = str(document.id)

    # Drop the previous generation of chunks and its index entries so a
    # re-index cannot leave stale text behind.
    await db.execute(delete(Chunk).where(Chunk.document_id == document.id))
    await db.flush()
    hybrid_index.delete_document(document_id)

    if not text.strip():
        logger.info("Document %s has no content; nothing indexed", document_id)
        return []

    metadata = _document_metadata(document)
    pieces = chunker.chunk(text, metadata)
    if not pieces:
        return []

    rows = [
        Chunk(
            document_id=document.id,
            kb_id=document.kb_id,
            content=piece["content"],
            chunk_index=piece["chunk_index"],
            chunk_size=len(piece["content"]),
            token_count=piece["token_count"],
            data={
                "title": document.title,
                "source_type": document.source_type,
                "start_char": piece["start_char"],
                "end_char": piece["end_char"],
            },
        )
        for piece in pieces
    ]
    db.add_all(rows)
    await db.flush()

    vectors = embedding_service.embed([row.content for row in rows])
    entries = []
    for row, vector in zip(rows, vectors):
        row.embedding = vector
        entries.append(
            build_entry(
                chunk_id=str(row.id),
                document_id=document_id,
                content=row.content,
                metadata={**metadata, "chunk_index": row.chunk_index},
                title=document.title,
                kb_id=str(document.kb_id),
                chunk_index=row.chunk_index,
                token_count=row.token_count or 0,
            )
        )

    hybrid_index.index_chunks(entries)
    logger.info("Indexed %d chunks for document %s", len(entries), document_id)
    return [entry["chunk_id"] for entry in entries]


async def remove_document(db: AsyncSession, document_id: UUID) -> None:
    """Delete a document's chunks from Postgres and from the index."""
    await db.execute(delete(Chunk).where(Chunk.document_id == document_id))
    hybrid_index.delete_document(str(document_id))


async def rehydrate_index(db: AsyncSession) -> int:
    """Rebuild the in-process index from Postgres.

    Called on startup: the index is per-process state, so without this a restart
    would serve an empty index even though the chunks are still stored.
    Embeddings come from the ``Chunk.embedding`` column, so no model is called;
    rows without a stored vector fall back to being embedded on the spot.
    """
    hybrid_index.clear()

    result = await db.execute(
        select(Chunk, Document.title, Document.source_type)
        .join(Document, Document.id == Chunk.document_id)
    )
    rows = result.all()
    if not rows:
        return 0

    entries: List[Dict[str, Any]] = []
    vectors: List[Optional[List[float]]] = []
    needs_embedding: List[int] = []

    for chunk, title, source_type in rows:
        entries.append(
            build_entry(
                chunk_id=str(chunk.id),
                document_id=str(chunk.document_id),
                content=chunk.content,
                metadata={
                    **(chunk.data or {}),
                    "kb_id": str(chunk.kb_id),
                    "title": title,
                    "source_type": source_type,
                    "chunk_index": chunk.chunk_index,
                },
                title=title,
                kb_id=str(chunk.kb_id),
                chunk_index=chunk.chunk_index or 0,
                token_count=chunk.token_count or 0,
            )
        )
        vectors.append(chunk.embedding)
        if not chunk.embedding:
            needs_embedding.append(len(entries) - 1)

    if needs_embedding:
        logger.warning("Re-embedding %d chunks that had no stored vector", len(needs_embedding))
        fresh = embedding_service.embed([entries[position]["content"] for position in needs_embedding])
        for position, vector in zip(needs_embedding, fresh):
            vectors[position] = vector

    hybrid_index.index_chunks(entries, vectors)

    logger.info("Rehydrated %d chunks from Postgres", len(entries))
    return len(entries)