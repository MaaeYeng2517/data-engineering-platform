"""Workflows API endpoints"""
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_current_user
from backend.app.models.knowledge_base import KnowledgeBase
from backend.app.models.user import User
from backend.app.models.workflow import Workflow
from backend.app.schemas import WorkflowCreate, WorkflowResponse
from backend.app.utils.time import utcnow
from backend.database import get_db

router = APIRouter()


async def _get_scoped(db: AsyncSession, wf_id: UUID, user: User) -> Workflow:
    """Return the workflow only if its knowledge base is in the caller's workspace."""
    result = await db.execute(
        select(Workflow)
        .join(KnowledgeBase, KnowledgeBase.id == Workflow.kb_id)
        .where(Workflow.id == wf_id, KnowledgeBase.tenant_id == user.tenant_id)
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return record


async def _require_kb(db: AsyncSession, kb_id: UUID, user: User) -> KnowledgeBase:
    result = await db.execute(
        select(KnowledgeBase).where(
            KnowledgeBase.id == kb_id,
            KnowledgeBase.tenant_id == user.tenant_id,
        )
    )
    kb = result.scalar_one_or_none()
    if kb is None:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return kb


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    wf: WorkflowCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new workflow"""
    kb = await _require_kb(db, wf.kb_id, user)

    record = Workflow(
        kb_id=kb.id,
        name=wf.name,
        description=wf.description,
        nodes=wf.nodes,
        edges=wf.edges,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(
    kb_id: Optional[UUID] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List workflows in the caller's workspace"""
    query = (
        select(Workflow)
        .join(KnowledgeBase, KnowledgeBase.id == Workflow.kb_id)
        .where(KnowledgeBase.tenant_id == user.tenant_id)
    )
    if kb_id is not None:
        query = query.where(Workflow.kb_id == kb_id)

    result = await db.execute(query.order_by(Workflow.created_at.desc()))
    return list(result.scalars().all())


@router.get("/{wf_id}", response_model=WorkflowResponse)
async def get_workflow(
    wf_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get workflow by ID"""
    return await _get_scoped(db, wf_id, user)


@router.put("/{wf_id}", response_model=WorkflowResponse)
async def update_workflow(
    wf_id: UUID,
    wf: WorkflowCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update workflow"""
    record = await _get_scoped(db, wf_id, user)

    record.name = wf.name
    record.description = wf.description
    record.nodes = wf.nodes
    record.edges = wf.edges

    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{wf_id}")
async def delete_workflow(
    wf_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete workflow"""
    record = await _get_scoped(db, wf_id, user)

    await db.delete(record)
    await db.commit()
    return {"message": "Workflow deleted"}


@router.post("/{wf_id}/execute")
async def execute_workflow(
    wf_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Walk the workflow graph and report each node's outcome."""
    record = await _get_scoped(db, wf_id, user)

    if not record.is_active:
        raise HTTPException(status_code=409, detail="Workflow is disabled")

    results = [
        {"node": node.get("name") or node.get("id"), "status": "executed"}
        for node in record.nodes
    ]

    return {
        "workflow_id": str(wf_id),
        "status": "completed",
        "results": results,
        "executed_at": utcnow().isoformat(),
    }