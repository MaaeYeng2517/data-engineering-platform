"""Evaluation API endpoints"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.utils.time import utcnow
from backend.app.dependencies import get_current_user
from backend.app.models.evaluation import EvaluationDataset, EvaluationRun
from backend.app.models.user import User
from backend.app.schemas import EvaluationRequest, EvaluationResponse
from backend.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_dataset(db: AsyncSession, dataset_id: UUID, user: User) -> EvaluationDataset:
    """Get dataset by ID, scoped to user's tenant."""
    result = await db.execute(
        select(EvaluationDataset).where(
            EvaluationDataset.id == dataset_id,
            EvaluationDataset.tenant_id == user.tenant_id,
        )
    )
    dataset = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset


@router.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluationRequest):
    """Run evaluation on knowledge base"""
    from backend.app.services.evaluation import evaluation_engine
    
    result = await evaluation_engine.evaluate(
        str(request.kb_id),
        str(request.dataset_id) if request.dataset_id else None,
        request.questions
    )
    
    return {
        "run_id": f"run_{utcnow().timestamp()}",
        "metrics": result["metrics"],
        "overall_score": result["metrics"]["overall_score"],
        "results": result["results"],
        "status": "completed"
    }


@router.post("/datasets", response_model=dict, status_code=201)
async def create_dataset(
    kb_id: UUID,
    name: str,
    questions: List[dict],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create evaluation dataset"""
    from backend.app.services.evaluation import evaluation_engine
    
    dataset = EvaluationDataset(
        tenant_id=user.tenant_id,
        kb_id=kb_id,
        name=name,
        questions=questions,
    )
    db.add(dataset)
    await db.commit()
    await db.refresh(dataset)
    
    return {
        "id": str(dataset.id),
        "kb_id": str(dataset.kb_id),
        "name": dataset.name,
        "question_count": len(dataset.questions or []),
        "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
    }


@router.get("/datasets", response_model=List[dict])
async def list_datasets(
    kb_id: Optional[UUID] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List evaluation datasets"""
    query = select(EvaluationDataset).where(EvaluationDataset.tenant_id == user.tenant_id)
    if kb_id:
        query = query.where(EvaluationDataset.kb_id == kb_id)
    query = query.order_by(EvaluationDataset.created_at.desc())
    
    result = await db.execute(query)
    datasets = result.scalars().all()
    
    return [
        {
            "id": str(d.id),
            "kb_id": str(d.kb_id),
            "name": d.name,
            "question_count": len(d.questions or []),
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "updated_at": d.updated_at.isoformat() if d.updated_at else None,
        }
        for d in datasets
    ]


@router.get("/datasets/{dataset_id}", response_model=dict)
async def get_dataset(
    dataset_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get evaluation dataset by ID"""
    dataset = await _get_dataset(db, dataset_id, user)
    return {
        "id": str(dataset.id),
        "kb_id": str(dataset.kb_id),
        "name": dataset.name,
        "questions": dataset.questions,
        "question_count": len(dataset.questions or []),
        "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
        "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None,
    }


@router.put("/datasets/{dataset_id}", response_model=dict)
async def update_dataset(
    dataset_id: UUID,
    name: Optional[str] = None,
    questions: Optional[List[dict]] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update evaluation dataset"""
    dataset = await _get_dataset(db, dataset_id, user)
    
    if name is not None:
        dataset.name = name
    if questions is not None:
        dataset.questions = questions
    
    await db.commit()
    await db.refresh(dataset)
    
    return {
        "id": str(dataset.id),
        "kb_id": str(dataset.kb_id),
        "name": dataset.name,
        "question_count": len(dataset.questions or []),
        "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None,
    }


@router.delete("/datasets/{dataset_id}", status_code=204)
async def delete_dataset(
    dataset_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete evaluation dataset"""
    dataset = await _get_dataset(db, dataset_id, user)
    await db.delete(dataset)
    await db.commit()


@router.get("/runs", response_model=List[dict])
async def list_runs(
    dataset_id: Optional[UUID] = None,
    kb_id: Optional[UUID] = None,
    limit: int = Query(50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List evaluation runs"""
    query = select(EvaluationRun).where(EvaluationRun.tenant_id == user.tenant_id)
    if dataset_id:
        query = query.where(EvaluationRun.dataset_id == dataset_id)
    if kb_id:
        query = query.where(EvaluationRun.kb_id == kb_id)
    query = query.order_by(EvaluationRun.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    runs = result.scalars().all()
    
    return [
        {
            "id": str(r.id),
            "dataset_id": str(r.dataset_id) if r.dataset_id else None,
            "kb_id": str(r.kb_id) if r.kb_id else None,
            "metrics": r.metrics,
            "overall_score": r.overall_score,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]


@router.get("/runs/{run_id}", response_model=dict)
async def get_run(
    run_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get evaluation run by ID"""
    result = await db.execute(
        select(EvaluationRun).where(
            EvaluationRun.id == run_id,
            EvaluationRun.tenant_id == user.tenant_id,
        )
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    
    return {
        "id": str(run.id),
        "dataset_id": str(run.dataset_id) if run.dataset_id else None,
        "kb_id": str(run.kb_id) if run.kb_id else None,
        "metrics": run.metrics,
        "overall_score": run.overall_score,
        "results": run.results,
        "status": run.status,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }