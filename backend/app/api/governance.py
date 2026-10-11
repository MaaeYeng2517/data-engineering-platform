"""Governance API endpoints"""
import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.utils.time import utcnow
from backend.app.dependencies import get_current_user
from backend.app.models.governance import GovernancePolicy, ApprovalWorkflow
from backend.app.models.user import User
from backend.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


async def _get_policy(db: AsyncSession, policy_id: UUID, user: User) -> GovernancePolicy:
    """Get policy by ID, scoped to user's tenant."""
    result = await db.execute(
        select(GovernancePolicy).where(
            GovernancePolicy.id == policy_id,
            GovernancePolicy.tenant_id == user.tenant_id,
        )
    )
    policy = result.scalar_one_or_none()
    if policy is None:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


async def _get_approval(db: AsyncSession, approval_id: UUID, user: User) -> ApprovalWorkflow:
    """Get approval by ID, scoped to user's tenant."""
    result = await db.execute(
        select(ApprovalWorkflow).where(
            ApprovalWorkflow.id == approval_id,
            ApprovalWorkflow.tenant_id == user.tenant_id,
        )
    )
    approval = result.scalar_one_or_none()
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return approval


@router.get("/permissions")
async def get_permissions():
    """Get available permissions"""
    from backend.app.services.governance import governance
    
    return {
        "permissions": [p.value for p in governance.roles.keys()]
    }


@router.get("/roles")
async def get_roles():
    """Get available roles"""
    from backend.app.services.governance import governance
    
    return {
        "roles": [
            {
                "name": role.value,
                "permissions": [p.value for p in permissions]
            }
            for role, permissions in governance.roles.items()
        ]
    }


# --- Policies CRUD ---

@router.post("/policies", response_model=dict, status_code=201)
async def create_policy(
    name: str,
    rules: dict,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a governance policy"""
    from backend.app.services.governance import governance
    
    governance.policy.define_policy(name, rules)
    
    policy = GovernancePolicy(
        tenant_id=user.tenant_id,
        name=name,
        rules=rules,
        created_by=user.id,
    )
    db.add(policy)
    await db.commit()
    await db.refresh(policy)
    
    return {
        "id": str(policy.id),
        "name": policy.name,
        "rules": policy.rules,
        "created_by": str(policy.created_by),
        "created_at": policy.created_at.isoformat() if policy.created_at else None,
    }


@router.get("/policies", response_model=List[dict])
async def list_policies(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List governance policies"""
    result = await db.execute(
        select(GovernancePolicy)
        .where(GovernancePolicy.tenant_id == user.tenant_id)
        .order_by(GovernancePolicy.created_at.desc())
    )
    policies = result.scalars().all()
    
    return [
        {
            "id": str(p.id),
            "name": p.name,
            "rules": p.rules,
            "created_by": str(p.created_by) if p.created_by else None,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "updated_at": p.updated_at.isoformat() if p.updated_at else None,
        }
        for p in policies
    ]


@router.get("/policies/{policy_id}", response_model=dict)
async def get_policy(
    policy_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get governance policy by ID"""
    policy = await _get_policy(db, policy_id, user)
    return {
        "id": str(policy.id),
        "name": policy.name,
        "rules": policy.rules,
        "created_by": str(policy.created_by) if policy.created_by else None,
        "created_at": policy.created_at.isoformat() if policy.created_at else None,
        "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
    }


@router.put("/policies/{policy_id}", response_model=dict)
async def update_policy(
    policy_id: UUID,
    name: Optional[str] = None,
    rules: Optional[dict] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update governance policy"""
    from backend.app.services.governance import governance
    
    policy = await _get_policy(db, policy_id, user)
    
    if name is not None:
        policy.name = name
    if rules is not None:
        policy.rules = rules
        governance.policy.define_policy(policy.name, rules)
    
    await db.commit()
    await db.refresh(policy)
    
    return {
        "id": str(policy.id),
        "name": policy.name,
        "rules": policy.rules,
        "updated_at": policy.updated_at.isoformat() if policy.updated_at else None,
    }


@router.delete("/policies/{policy_id}", status_code=204)
async def delete_policy(
    policy_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete governance policy"""
    policy = await _get_policy(db, policy_id, user)
    await db.delete(policy)
    await db.commit()


# --- Approvals CRUD ---

@router.post("/approvals", response_model=dict)
async def submit_approval(
    kb_id: str,
    document_id: str,
    creator_id: str,
    reviewers: List[str],
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit document for approval"""
    from backend.app.services.governance import governance
    
    approval = governance.approval.submit_for_approval(
        kb_id, document_id, creator_id, reviewers
    )
    
    # Also persist to database
    approval_record = ApprovalWorkflow(
        tenant_id=user.tenant_id,
        kb_id=UUID(kb_id),
        document_id=UUID(document_id),
        creator_id=UUID(creator_id),
        reviewers=[UUID(r) for r in reviewers],
        status="pending",
    )
    db.add(approval_record)
    await db.commit()
    await db.refresh(approval_record)
    
    return {
        "id": str(approval_record.id),
        "kb_id": str(approval_record.kb_id),
        "document_id": str(approval_record.document_id),
        "creator_id": str(approval_record.creator_id),
        "reviewers": [str(r) for r in approval_record.reviewers or []],
        "status": approval_record.status,
        "created_at": approval_record.created_at.isoformat() if approval_record.created_at else None,
    }


@router.get("/approvals", response_model=List[dict])
async def list_approvals(
    status: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List approval workflows"""
    query = select(ApprovalWorkflow).where(ApprovalWorkflow.tenant_id == user.tenant_id)
    if status:
        query = query.where(ApprovalWorkflow.status == status)
    query = query.order_by(ApprovalWorkflow.created_at.desc())
    
    result = await db.execute(query)
    approvals = result.scalars().all()
    
    return [
        {
            "id": str(a.id),
            "kb_id": str(a.kb_id),
            "document_id": str(a.document_id),
            "creator_id": str(a.creator_id),
            "reviewers": [str(r) for r in a.reviewers or []],
            "status": a.status,
            "decision": a.decision,
            "comments": a.comments,
            "decided_by": str(a.decided_by) if a.decided_by else None,
            "decided_at": a.decided_at.isoformat() if a.decided_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None,
        }
        for a in approvals
    ]


@router.get("/approvals/{approval_id}", response_model=dict)
async def get_approval(
    approval_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get approval by ID"""
    approval = await _get_approval(db, approval_id, user)
    return {
        "id": str(approval.id),
        "kb_id": str(approval.kb_id),
        "document_id": str(approval.document_id),
        "creator_id": str(approval.creator_id),
        "reviewers": [str(r) for r in approval.reviewers or []],
        "status": approval.status,
        "decision": approval.decision,
        "comments": approval.comments,
        "decided_by": str(approval.decided_by) if approval.decided_by else None,
        "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
        "created_at": approval.created_at.isoformat() if approval.created_at else None,
        "updated_at": approval.updated_at.isoformat() if approval.updated_at else None,
    }


@router.post("/approvals/{approval_id}/approve", response_model=dict)
async def approve_document(
    approval_id: UUID,
    reviewer_id: str,
    comments: str = "",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve a document"""
    from backend.app.services.governance import governance
    
    approval = await _get_approval(db, approval_id, user)
    
    # Verify the current user is one of the reviewers
    if UUID(reviewer_id) not in (approval.reviewers or []):
        raise HTTPException(status_code=403, detail="User is not a reviewer for this approval")
    
    result = governance.approval.approve(approval_id, reviewer_id, comments)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # Update database record
    approval.status = "approved"
    approval.decision = "approved"
    approval.comments = comments
    approval.decided_by = UUID(reviewer_id)
    approval.decided_at = utcnow()
    
    await db.commit()
    await db.refresh(approval)
    
    return {
        "id": str(approval.id),
        "status": approval.status,
        "decision": approval.decision,
        "comments": approval.comments,
        "decided_by": str(approval.decided_by),
        "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
    }


@router.post("/approvals/{approval_id}/reject", response_model=dict)
async def reject_document(
    approval_id: UUID,
    reviewer_id: str,
    comments: str = "",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a document"""
    from backend.app.services.governance import governance
    
    approval = await _get_approval(db, approval_id, user)
    
    # Verify the current user is one of the reviewers
    if UUID(reviewer_id) not in (approval.reviewers or []):
        raise HTTPException(status_code=403, detail="User is not a reviewer for this approval")
    
    result = governance.approval.reject(approval_id, reviewer_id, comments)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    # Update database record
    approval.status = "rejected"
    approval.decision = "rejected"
    approval.comments = comments
    approval.decided_by = UUID(reviewer_id)
    approval.decided_at = utcnow()
    
    await db.commit()
    await db.refresh(approval)
    
    return {
        "id": str(approval.id),
        "status": approval.status,
        "decision": approval.decision,
        "comments": approval.comments,
        "decided_by": str(approval.decided_by),
        "decided_at": approval.decided_at.isoformat() if approval.decided_at else None,
    }


@router.get("/audit")
async def get_audit_logs(
    user_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get audit logs"""
    from backend.app.services.governance import governance
    
    logs = governance.audit.get_logs(user_id=user_id, limit=limit)
    
    return {
        "logs": logs,
        "total": len(logs)
    }