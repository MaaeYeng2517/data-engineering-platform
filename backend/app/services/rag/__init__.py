"""Context engineering layer"""
from typing import Any, Dict, List, Optional
import logging
from backend.app.utils.time import utcnow

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Build context for LLM from retrieved documents"""
    
    def __init__(self, max_tokens: int = 4000):
        self.max_tokens = max_tokens
    
    async def build(self, query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build context from search results"""
        # Deduplication
        deduplicated = await self._deduplicate(results)

        # Relevance filter
        relevant = await self._filter_relevance(query, deduplicated)

        # Context compression
        compressed = await self._compress(relevant)

        # Context ordering
        ordered = await self._order(compressed)

        # Context budget
        final_context = await self._apply_budget(ordered)

        return {
            "context": final_context,
            "sources": [
                result.get("document_id") or result.get("doc_id") or result.get("chunk_id", "")
                for result in final_context
            ],
            "total_tokens": sum(
                result.get("token_count") or len(result.get("content", "").split())
                for result in final_context
            ),
            "built_at": utcnow().isoformat(),
        }
    
    async def _deduplicate(self, results: List[Dict]) -> List[Dict]:
        """Remove duplicate chunks"""
        seen = set()
        unique = []
        
        for result in results:
            chunk_id = result.get("chunk_id") or result.get("doc_id")
            if chunk_id and chunk_id not in seen:
                seen.add(chunk_id)
                unique.append(result)
        
        return unique
    
    async def _filter_relevance(self, query: str, results: List[Dict]) -> List[Dict]:
        """Drop passages that carry no relevance signal.

        Retrieval always sets ``score``, but a caller can hand results straight
        to the builder, so fall back to whichever score is present rather than
        discarding everything.
        """
        def relevance(result: Dict) -> float:
            for key in ("score", "rerank_score", "hybrid_score"):
                value = result.get(key)
                if isinstance(value, (int, float)):
                    return float(value)
            return 0.0

        return [result for result in results if relevance(result) > 0.1]
    
    async def _compress(self, results: List[Dict]) -> List[Dict]:
        """Compress context by truncating long content"""
        compressed = []
        
        for result in results:
            content = result.get("content", "")
            if len(content) > 500:
                result["content"] = content[:500] + "..."
                result["token_count"] = len(result["content"].split())
            compressed.append(result)
        
        return compressed
    
    async def _order(self, results: List[Dict]) -> List[Dict]:
        """Order by relevance score"""
        return sorted(
            results,
            key=lambda result: result.get("score") or result.get("hybrid_score") or 0.0,
            reverse=True,
        )
    
    async def _apply_budget(self, results: List[Dict]) -> List[Dict]:
        """Apply token budget"""
        selected = []
        total_tokens = 0
        
        for result in results:
            tokens = result.get("token_count", len(result.get("content", "").split()))
            if total_tokens + tokens <= self.max_tokens:
                selected.append(result)
                total_tokens += tokens
            else:
                break
        
        return selected


class RAGEngine:
    """RAG pipeline for question answering"""
    
    def __init__(self):
        self.context_builder = ContextBuilder()
    
    async def answer(self, query: str, kb_ids: List[str], 
                    metadata_filters: Dict = None, limit: int = 5,
                    temperature: float = 0.7, max_tokens: int = 1000) -> Dict[str, Any]:
        """Generate answer using RAG"""
        from backend.app.services.retrieval import retrieval_engine
        
        # Retrieve relevant documents
        search_results = await retrieval_engine.search(
            query, kb_ids, metadata_filters, limit
        )
        
        # Build context
        context_data = await self.context_builder.build(query, search_results["results"])
        
        # Generate answer (placeholder - in production, use LLM)
        answer = await self._generate_answer(query, context_data, temperature, max_tokens)
        
        # Extract citations
        citations = await self._extract_citations(context_data)
        
        return {
            "answer": answer,
            "sources": search_results["results"],
            "citations": citations,
            "latency_ms": search_results["latency_ms"],
            "token_usage": {
                "prompt": context_data["total_tokens"],
                "completion": len(answer.split()),
                "total": context_data["total_tokens"] + len(answer.split())
            }
        }
    
    async def _generate_answer(self, query: str, context_data: Dict,
                              temperature: float, max_tokens: int) -> str:
        """Generate an answer with the configured LLM provider."""
        from backend.app.services.llm import LLMError, LLMMessage, llm_gateway

        context_blocks = [
            f"[{index}] {result['content']}"
            for index, result in enumerate(context_data["context"], start=1)
        ]
        system = (
            "You are the retrieval assistant for a knowledge platform. Answer only "
            "from the numbered context passages, cite them as [1], [2] and so on, and "
            "state plainly when the context does not contain the answer."
        )
        if context_blocks:
            system += "\n\nContext passages:\n" + "\n\n".join(context_blocks)

        try:
            result = await llm_gateway.generate(
                [LLMMessage(role="user", content=query)],
                system=system,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except LLMError as exc:
            logger.warning("Falling back to an extractive answer: %s", exc)
        else:
            if result.content.strip():
                return result.content

        return self._extractive_answer(query, context_data)
    
    async def _extractive_answer(self, query: str, context_data: Dict) -> str:
        """Last-resort answer that quotes the retrieved context verbatim."""
        passages = [
            f"[{index}] {result['content'][:300]}"
            for index, result in enumerate(context_data["context"], start=1)
        ]
        if not passages:
            return (
                f"No indexed passages matched '{query}'. Add documents to a knowledge "
                "base or broaden the query."
            )
        return (
            "No LLM provider is available to summarise the retrieved context, so here "
            f"it is quoted directly for '{query}':\n\n" + "\n\n".join(passages)
        )

    async def _extract_citations(self, context_data: Dict[str, Any]) -> List[Dict]:
        """Turn the selected passages into numbered citations."""
        citations = []
        for position, source in enumerate(context_data["context"], start=1):
            citations.append(
                {
                    "index": position,
                    "source": source.get("document_id")
                    or source.get("doc_id")
                    or source.get("chunk_id", ""),
                    "chunk_id": source.get("chunk_id", ""),
                    "title": source.get("title", ""),
                    "score": round(float(source.get("score", 0.0)), 6),
                    "content_preview": source.get("content", "")[:100],
                }
            )
        return citations


# Global RAG engine
rag_engine = RAGEngine()