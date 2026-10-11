"""Hybrid retrieval engine.

Sits between the raw indexes and the API: scopes a query to the requested
knowledge bases, applies metadata filters, reranks, and guarantees every hit
carries the fields the response model requires.
"""
from typing import Any, Dict, Iterable, List, Optional
import time
import logging

from backend.app.services import indexing

logger = logging.getLogger(__name__)
logger = logging.getLogger(__name__)

# How many candidates to pull from the index per requested result. Reranking
# can only reorder what it is given.
CANDIDATE_MULTIPLIER = 2


class MetadataFilter:
    """Filter results by exact metadata match."""

    def apply(self, results: List[Dict], filters: Dict[str, Any]) -> List[Dict]:
        if not filters:
            return results

        filtered = []
        for result in results:
            metadata = result.get("metadata", {})
            if all(metadata.get(key) == value or result.get(key) == value for key, value in filters.items()):
                filtered.append(result)
        return filtered


class Reranker:
    """Rerank results for better relevance."""

    def rerank(self, query: str, results: List[Dict], top_k: int = 10) -> List[Dict]:
        """Rerank results using lexical and positional signals.

        The rerank score becomes the result's ``score``, which is the only
        score the API contract exposes.
        """
        query_terms = {term for term in query.lower().split() if term}

        for position, result in enumerate(results):
            content = result.get("content", "").lower()
            content_terms = {term for term in content.split() if term}
            overlap = len(query_terms & content_terms)

            # Earlier hits are more likely to be the passage being looked for.
            position_bonus = 1.0 / (1 + result.get("position", position))

            # Too short to carry meaning, or so long it drowns the context.
            content_len = len(content)
            length_score = 1.0 if 100 < content_len < 1000 else 0.8

            result["rerank_score"] = (
                result.get("hybrid_score", 0.0) * 0.5
                + overlap * 0.3
                + position_bonus * 0.1
                + length_score * 0.1
            )
            result["score"] = result["rerank_score"]

        results.sort(key=lambda item: item.get("rerank_score", 0.0), reverse=True)
        return results[:top_k]


class RetrievalEngine:
    """Main retrieval engine."""

    def __init__(self, index=None):
        self.metadata_filter = MetadataFilter()
        self.reranker = Reranker()
        self._index = index

    @property
    def hybrid_index(self):
        return self._index if self._index is not None else indexing.hybrid_index

    async def search(
        self,
        query: str,
        kb_ids: Optional[Iterable[str]] = None,
        metadata_filters: Optional[Dict] = None,
        limit: int = 10,
        search_type: str = "hybrid",
        score_threshold: Optional[float] = None,
        db=None,
    ) -> Dict[str, Any]:
        """Perform hybrid search scoped to the given knowledge bases.

        When ``db`` is supplied and the in-memory index is empty, the index is
        rehydrated from Postgres first, so a freshly started API process (or one
        that has no documents indexed yet) can still answer.
        """
        start_time = time.time()

        if db is not None and len(self.hybrid_index) == 0:
            try:
                from backend.app.services.indexing.pipeline import rehydrate_index

                await rehydrate_index(db)
            except Exception:
                logger.warning("Lazy index rehydration failed", exc_info=True)

        candidates = self.hybrid_index.search(
            query,
            limit=limit * CANDIDATE_MULTIPLIER,
            metadata_filter=metadata_filters,
            kb_ids=kb_ids,
        )

        if metadata_filters:
            candidates = self.metadata_filter.apply(candidates, metadata_filters)

        candidates = self.reranker.rerank(query, candidates, limit)

        if score_threshold is not None:
            candidates = [
                result for result in candidates if result.get("score", 0.0) >= score_threshold
            ]

        latency = (time.time() - start_time) * 1000

        return {
            "query": query,
            "results": candidates,
            "total": len(candidates),
            "latency_ms": latency,
            "search_type": search_type,
        }

    async def keyword_search(
        self,
        query: str,
        limit: int = 10,
        kb_ids: Optional[Iterable[str]] = None,
        metadata_filter: Optional[Dict] = None,
    ) -> List[Dict]:
        """Keyword-only search."""
        results = self.keyword_index_search(query, limit, metadata_filter)
        return self._scope(results, kb_ids, limit)

    async def vector_search(
        self,
        query: str,
        limit: int = 10,
        kb_ids: Optional[Iterable[str]] = None,
        metadata_filter: Optional[Dict] = None,
    ) -> List[Dict]:
        """Vector-only search."""
        results = self.vector_index_search(query, limit, metadata_filter)
        return self._scope(results, kb_ids, limit)

    async def graph_search(self, query: str, limit: int = 10) -> List[Dict]:
        """Graph-based search over indexed entities."""
        return self.hybrid_index.graph_index.search(query, limit)

    def keyword_index_search(
        self,
        query: str,
        limit: int = 10,
        metadata_filter: Optional[Dict] = None,
    ) -> List[Dict]:
        return self.hybrid_index.keyword_index.search(query, limit, metadata_filter)

    def vector_index_search(
        self,
        query: str,
        limit: int = 10,
        metadata_filter: Optional[Dict] = None,
    ) -> List[Dict]:
        return self.hybrid_index.vector_index.search(query, limit, metadata_filter)

    @staticmethod
    def _scope(
        results: List[Dict],
        kb_ids: Optional[Iterable[str]],
        limit: int,
    ) -> List[Dict]:
        """Keep only hits inside the requested knowledge bases."""
        if not kb_ids:
            return results[:limit]

        allowed = {str(kb_id) for kb_id in kb_ids}
        scoped = [result for result in results if str(result.get("kb_id") or "") in allowed]
        return scoped[:limit]


# Global retrieval engine
retrieval_engine = RetrievalEngine()