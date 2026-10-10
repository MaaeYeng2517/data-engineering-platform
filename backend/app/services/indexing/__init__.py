"""Indexing layer for hybrid search.

The index is chunk-centric: one entry per chunk, keyed by the chunk's database
UUID, and every entry carries the metadata the API needs to answer with
``chunk_id``/``document_id``/``title`` without a second lookup. Keyword and
vector halves therefore share keys, which is what makes the hybrid blend
meaningful — previously keyword results were keyed by document id and vector
results by chunk id, so the two halves almost never met.

The index lives in the process that serves search. `pipeline.rehydrate_index()`
rebuilds it from Postgres on startup, so a restart does not lose the index and
an embedding does not have to be recomputed.
"""
from typing import Any, Dict, Iterable, List, Optional
import logging

import numpy as np

from backend.app.utils.time import utcnow
from backend.app.services.embedding import embedding_service

logger = logging.getLogger(__name__)

# Weights used to blend the keyword and vector halves. Keyword matches are
# sparse and high-signal, vector similarity is dense, so the vector side leads.
KEYWORD_WEIGHT = 0.4
VECTOR_WEIGHT = 0.6

# How many candidates each sub-index contributes before blending. The hybrid
# ranking is only as good as the candidates it gets to compare.
CANDIDATE_MULTIPLIER = 4


def build_entry(
    chunk_id: str,
    document_id: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    title: str = "",
    kb_id: str = "",
    chunk_index: int = 0,
    token_count: int = 0,
) -> Dict[str, Any]:
    """Build the canonical index entry for one chunk.

    Every sub-index stores this dict, so all of them agree on the shape of a
    result and on which document/knowledge base a chunk belongs to.
    """
    metadata = dict(metadata or {})
    metadata.setdefault("document_id", document_id)
    if kb_id:
        metadata.setdefault("kb_id", kb_id)
    return {
        "chunk_id": chunk_id,
        "document_id": document_id,
        "kb_id": kb_id or metadata.get("kb_id", ""),
        "title": title,
        "content": content,
        "chunk_index": chunk_index,
        "token_count": token_count,
        "metadata": metadata,
        "indexed_at": utcnow().isoformat(),
    }


def _matches(entry: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    """Every filter key must be present on the entry and equal."""
    metadata = entry.get("metadata", {})
    for key, value in filters.items():
        if metadata.get(key) != value and entry.get(key) != value:
            return False
    return True


class KeywordIndex:
    """Term-frequency keyword index over chunks.

    Scoring is term frequency damped by document length
    (``1 / (1 + occurrences)``) rather than BM25: there is no corpus-level IDF
    table to maintain here, and the ranking is only ever combined with the
    vector score, never shown alone as a relevance judgement.
    """

    def __init__(self):
        self.chunks: Dict[str, Dict[str, Any]] = {}

    def __len__(self) -> int:
        return len(self.chunks)

    def index_chunk(self, entry: Dict[str, Any]) -> None:
        self.chunks[entry["chunk_id"]] = entry

    def index(self, doc_id: str, content: str, metadata: Optional[Dict] = None) -> str:
        """Index a single piece of text as its own chunk.

        Kept for callers that have one blob rather than a chunked document;
        ``doc_id`` doubles as the chunk id.
        """
        entry = build_entry(doc_id, doc_id, content, metadata)
        self.index_chunk(entry)
        return doc_id

    def search(
        self,
        query: str,
        limit: int = 10,
        metadata_filter: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        terms = [term for term in query.lower().split() if term]

        for chunk_id, entry in self.chunks.items():
            if metadata_filter and not _matches(entry, metadata_filter):
                continue

            content_lower = entry["content"].lower()
            score = 0.0
            for term in terms:
                occurrences = content_lower.count(term)
                if occurrences:
                    score += 1.0 / (1 + occurrences)

            if score > 0:
                results.append({**entry, "score": score})

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:limit]

    def delete(self, chunk_id: str) -> None:
        self.chunks.pop(chunk_id, None)

    def delete_document(self, document_id: str) -> int:
        return _delete_by_document(self.chunks, document_id)


class VectorIndex:
    """Cosine-similarity index over chunk embeddings."""

    def __init__(self):
        self.collection_name = "knowledge_chunks"
        self.embeddings: Dict[str, List[float]] = {}
        self.chunk_store: Dict[str, Dict[str, Any]] = {}
        self._service = embedding_service
        self.dim = self._service.vector_size

    def __len__(self) -> int:
        return len(self.embeddings)

    def _generate_embedding(self, text: str) -> List[float]:
        return self._service.embed_query(text)

    def index_chunk(self, entry: Dict[str, Any], embedding: Optional[List[float]] = None) -> None:
        chunk_id = entry["chunk_id"]
        self.embeddings[chunk_id] = embedding or self._generate_embedding(entry["content"])
        self.chunk_store[chunk_id] = entry

    def index_chunks(
        self,
        chunks: Iterable[Dict[str, Any]],
        embeddings: Optional[Iterable[List[float]]] = None,
    ) -> List[str]:
        """Batch-index chunk entries.

        ``embeddings`` short-circuits the embedding call, which is what
        rehydrating from stored vectors needs.
        """
        entries = list(chunks)
        if not entries:
            return []

        if embeddings is None:
            vectors = self._service.embed([entry["content"] for entry in entries])
        else:
            vectors = list(embeddings)

        for entry, embedding in zip(entries, vectors):
            self.index_chunk(entry, embedding)

        logger.info("Indexed %d chunks", len(entries))
        return [entry["chunk_id"] for entry in entries]

    def search(
        self,
        query: str,
        limit: int = 10,
        metadata_filter: Optional[Dict] = None,
    ) -> List[Dict[str, Any]]:
        query_embedding = self._generate_embedding(query)
        results: List[Dict[str, Any]] = []

        for chunk_id, embedding in self.embeddings.items():
            entry = self.chunk_store.get(chunk_id)
            if entry is None:
                continue
            if metadata_filter and not _matches(entry, metadata_filter):
                continue

            results.append({**entry, "score": self._cosine_similarity(query_embedding, embedding)})

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:limit]

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        v1 = np.array(vec1, dtype=np.float64)
        v2 = np.array(vec2, dtype=np.float64)

        norm_v1 = float(np.linalg.norm(v1))
        norm_v2 = float(np.linalg.norm(v2))
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0

        return float(np.dot(v1, v2)) / (norm_v1 * norm_v2)

    def delete(self, chunk_id: str) -> None:
        self.embeddings.pop(chunk_id, None)
        self.chunk_store.pop(chunk_id, None)

    def delete_document(self, document_id: str) -> int:
        doomed = _ids_for_document(self.chunk_store, document_id)
        for chunk_id in doomed:
            self.chunk_store.pop(chunk_id, None)
            self.embeddings.pop(chunk_id, None)
        return len(doomed)


class MetadataIndex:
    """Registry of chunk metadata, used for filter-only lookups."""

    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}

    def __len__(self) -> int:
        return len(self._store)

    def index_chunk(self, entry: Dict[str, Any]) -> None:
        self._store[entry["chunk_id"]] = entry["metadata"]

    def index(self, doc_id: str, metadata: Optional[Dict] = None) -> None:
        """Back-compat helper for callers holding a single metadata blob."""
        self._store[doc_id] = dict(metadata or {})

    def search(self, filters: Dict[str, Any], limit: int = 10) -> List[str]:
        matches = [
            chunk_id
            for chunk_id, metadata in self._store.items()
            if all(metadata.get(key) == value for key, value in filters.items())
        ]
        return matches[:limit]

    def delete(self, chunk_id: str) -> None:
        self._store.pop(chunk_id, None)

    def delete_document(self, document_id: str) -> int:
        return _delete_by_document(self._store, document_id, key="document_id")


class GraphIndex:
    """Entity-name lookup for graph search."""

    def __init__(self):
        self.graph: Dict[str, Dict[str, Any]] = {}

    def index(self, entity_id: str, entity_data: Dict[str, Any]) -> None:
        self.graph[entity_id] = entity_data

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        query_lower = query.lower()
        results = [
            {
                "entity_id": entity_id,
                "name": data.get("name", ""),
                "type": data.get("type", ""),
                "score": 1.0,
            }
            for entity_id, data in self.graph.items()
            if query_lower in data.get("name", "").lower()
        ]
        return results[:limit]


def _ids_for_document(
    store: Dict[str, Any],
    document_id: str,
    key: str = "document_id",
) -> List[str]:
    """Every entry id in a store whose entry belongs to a document."""
    return [
        entry_id
        for entry_id, entry in store.items()
        if isinstance(entry, dict) and entry.get(key) == document_id
    ]


def _delete_by_document(
    store: Dict[str, Any],
    document_id: str,
    key: str = "document_id",
) -> int:
    """Drop every entry belonging to a document and return how many went."""
    doomed = _ids_for_document(store, document_id, key)
    for entry_id in doomed:
        store.pop(entry_id, None)
    return len(doomed)


class HybridIndex:
    """Blends the keyword and vector indexes over shared chunk keys."""

    def __init__(self):
        self.keyword_index = KeywordIndex()
        self.vector_index = VectorIndex()
        self.metadata_index = MetadataIndex()
        self.graph_index = GraphIndex()

    def __len__(self) -> int:
        return len(self.vector_index)

    def index_chunks(
        self,
        chunks: Iterable[Dict[str, Any]],
        embeddings: Optional[Iterable[List[float]]] = None,
    ) -> List[str]:
        """Index a batch of chunk entries in every sub-index."""
        entries = list(chunks)
        if not entries:
            return []

        for entry in entries:
            self.keyword_index.index_chunk(entry)
            self.metadata_index.index_chunk(entry)

        return self.vector_index.index_chunks(entries, embeddings)

    def index(self, doc_id: str, content: str, metadata: Optional[Dict] = None) -> str:
        """Index one blob of text as a single chunk."""
        entry = build_entry(doc_id, doc_id, content, metadata)
        self.keyword_index.index_chunk(entry)
        self.metadata_index.index_chunk(entry)
        self.vector_index.index_chunk(entry)
        return doc_id

    def delete_document(self, document_id: str) -> int:
        """Remove every chunk of a document from all sub-indexes."""
        removed = self.vector_index.delete_document(document_id)
        self.keyword_index.delete_document(document_id)
        self.metadata_index.delete_document(document_id)
        return removed

    def clear(self) -> None:
        self.keyword_index = KeywordIndex()
        self.vector_index = VectorIndex()
        self.metadata_index = MetadataIndex()

    def chunk_count(self, kb_ids: Optional[Iterable[str]] = None) -> int:
        """How many chunks are in the index, optionally within some knowledge bases."""
        allowed = {str(kb_id) for kb_id in kb_ids} if kb_ids else None
        return sum(
            1
            for entry in self.vector_index.chunk_store.values()
            if allowed is None or str(entry.get("kb_id") or "") in allowed
        )

    def search(
        self,
        query: str,
        limit: int = 10,
        metadata_filter: Optional[Dict] = None,
        kb_ids: Optional[Iterable[str]] = None,
    ) -> List[Dict[str, Any]]:
        candidates = max(limit * CANDIDATE_MULTIPLIER, limit)
        keyword_results = self.keyword_index.search(query, candidates, metadata_filter)
        vector_results = self.vector_index.search(query, candidates, metadata_filter)

        allowed = {str(kb_id) for kb_id in kb_ids} if kb_ids else None
        combined: Dict[str, Dict[str, Any]] = {}

        for result in keyword_results:
            combined[result["chunk_id"]] = {
                **result,
                "keyword_score": result["score"],
                "vector_score": 0.0,
            }

        for result in vector_results:
            entry = combined.get(result["chunk_id"])
            if entry is None:
                combined[result["chunk_id"]] = {
                    **result,
                    "keyword_score": 0.0,
                    "vector_score": result["score"],
                }
            else:
                entry["vector_score"] = result["score"]

        results = []
        for entry in combined.values():
            if allowed is not None and str(entry.get("kb_id") or "") not in allowed:
                continue

            entry["hybrid_score"] = (
                entry["keyword_score"] * KEYWORD_WEIGHT
                + entry["vector_score"] * VECTOR_WEIGHT
            )
            entry["score"] = entry["hybrid_score"]
            # Do not return zero-score results - they don't match the query
            if entry["hybrid_score"] > 0:
                results.append(entry)

        results.sort(key=lambda item: item["hybrid_score"], reverse=True)
        return results[:limit]


# One index per process: the API process owns the copy that serves search.
hybrid_index = HybridIndex()