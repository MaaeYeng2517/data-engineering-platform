"""Search API endpoints"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas import SearchRequest, SearchResponse
from backend.database import get_db

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """Perform hybrid search scoped to the requested knowledge bases."""
    from backend.app.services.retrieval import retrieval_engine

    result = await retrieval_engine.search(
        request.query,
        kb_ids=[str(kb_id) for kb_id in request.kb_ids],
        metadata_filters=request.metadata_filters,
        limit=request.limit,
        search_type=request.search_type,
        score_threshold=request.score_threshold,
        db=db,
    )
    return result


@router.post("/keyword")
async def keyword_search(
    query: str,
    limit: int = Query(10, ge=1, le=100),
    kb_ids: Optional[List[UUID]] = Query(None),
):
    """Keyword-only search"""
    from backend.app.services.retrieval import retrieval_engine

    results = await retrieval_engine.keyword_search(
        query,
        limit,
        kb_ids=[str(kb_id) for kb_id in kb_ids] if kb_ids else None,
    )
    return {"query": query, "results": results, "total": len(results)}


@router.post("/vector")
async def vector_search(
    query: str,
    limit: int = Query(10, ge=1, le=100),
    kb_ids: Optional[List[UUID]] = Query(None),
):
    """Vector-only search"""
    from backend.app.services.retrieval import retrieval_engine

    results = await retrieval_engine.vector_search(
        query,
        limit,
        kb_ids=[str(kb_id) for kb_id in kb_ids] if kb_ids else None,
    )
    return {"query": query, "results": results, "total": len(results)}


@router.post("/graph")
async def graph_search(
    query: str,
    limit: int = Query(10, ge=1, le=100),
):
    """Graph-based search over indexed entities"""
    from backend.app.services.retrieval import retrieval_engine

    results = await retrieval_engine.graph_search(query, limit)
    return {"query": query, "results": results, "total": len(results)}