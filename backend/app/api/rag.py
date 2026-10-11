"""RAG API endpoints"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.schemas import RAGRequest, RAGResponse
from backend.database import get_db

router = APIRouter()


@router.post("/", response_model=RAGResponse)
async def rag_query(
    request: RAGRequest,
    db: AsyncSession = Depends(get_db),
):
    """Generate answer using RAG"""
    from backend.app.services.rag import rag_engine

    kb_ids_str = [str(kb_id) for kb_id in request.kb_ids]

    result = await rag_engine.answer(
        request.query,
        kb_ids_str,
        request.metadata_filters,
        request.limit,
        request.temperature,
        request.max_tokens,
        db=db,
    )

    return result