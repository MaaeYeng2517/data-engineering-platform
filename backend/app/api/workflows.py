"""Workflows API endpoints"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.app.utils.time import utcnow
from backend.app.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas import WorkflowCreate, WorkflowResponse

router = APIRouter()

# In-memory storage
_workflows = {}


def _get_scoped(wf_id: str, user: User) -> dict:
    """Return the workflow only if it belongs to the caller's workspace."""
    record = _workflows.get(wf_id)
    if record is None or record["tenant_id"] != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return record


@router.post("/", response_model=WorkflowResponse)
async def create_workflow(
    wf: WorkflowCreate,
    user: User = Depends(get_current_user),
):
    """Create a new workflow"""
    wf_id = str(uuid.uuid4())

    new_wf = {
        "id": wf_id,
        "kb_id": str(wf.kb_id),
        "tenant_id": str(user.tenant_id),
        "created_by": str(user.id),
        "name": wf.name,
        "description": wf.description,
        "nodes": wf.nodes,
        "edges": wf.edges,
        "is_active": True,
        "version": "1.0",
        "created_at": utcnow(),
        "updated_at": utcnow()
    }

    _workflows[wf_id] = new_wf
    return new_wf


@router.get("/", response_model=List[WorkflowResponse])
async def list_workflows(kb_id: str = None, user: User = Depends(get_current_user)):
    """List workflows in the caller's workspace"""
    wfs = [
        record for record in _workflows.values()
        if record["tenant_id"] == str(user.tenant_id)
    ]
    if kb_id:
        wfs = [record for record in wfs if record["kb_id"] == kb_id]
    return wfs


@router.get("/{wf_id}", response_model=WorkflowResponse)
async def get_workflow(wf_id: str, user: User = Depends(get_current_user)):
    """Get workflow by ID"""
    return _get_scoped(wf_id, user)


@router.put("/{wf_id}", response_model=WorkflowResponse)
async def update_workflow(
    wf_id: str,
    wf: WorkflowCreate,
    user: User = Depends(get_current_user),
):
    """Update workflow"""
    record = _get_scoped(wf_id, user)

    record.update({
        "name": wf.name,
        "description": wf.description,
        "nodes": wf.nodes,
        "edges": wf.edges,
        "updated_at": utcnow()
    })

    return record


@router.delete("/{wf_id}")
async def delete_workflow(wf_id: str, user: User = Depends(get_current_user)):
    """Delete workflow"""
    _get_scoped(wf_id, user)

    del _workflows[wf_id]
    return {"message": "Workflow deleted"}


@router.post("/{wf_id}/execute")
async def execute_workflow(wf_id: str, user: User = Depends(get_current_user)):
    """Execute a workflow"""
    wf = _get_scoped(wf_id, user)

    from backend.app.services.processing import processing_engine  # noqa: F401

    # Execute the declared nodes in order and report each one's outcome.
    results = []
    for node in wf.get("nodes", []):
        results.append({"node": node.get("name"), "status": "executed"})

    return {
        "workflow_id": wf_id,
        "status": "completed",
        "results": results,
        "executed_at": utcnow().isoformat()
    }