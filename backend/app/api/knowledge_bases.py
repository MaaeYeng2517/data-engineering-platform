"""Knowledge Bases API endpoints"""
import re
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.app.utils.time import utcnow
from backend.app.dependencies import get_current_user
from backend.app.models.user import User
from backend.app.schemas import KnowledgeBaseCreate, KnowledgeBaseResponse

router = APIRouter()

# In-memory storage
_kbs = {}


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "knowledge-base"


@router.post("/", response_model=KnowledgeBaseResponse)
async def create_kb(
    kb: KnowledgeBaseCreate,
    user: User = Depends(get_current_user),
):
    """Create a new knowledge base owned by the calling user."""
    kb_id = str(uuid.uuid4())

    new_kb = {
        "id": kb_id,
        "tenant_id": str(user.tenant_id),
        "owner_id": str(user.id),
        "name": kb.name,
        "description": kb.description,
        "slug": kb.slug or _slugify(kb.name),
        "settings": kb.settings,
        "is_published": False,
        "status": "draft",
        "version": "1.0",
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }

    _kbs[kb_id] = new_kb
    return new_kb


@router.get("/", response_model=List[KnowledgeBaseResponse])
async def list_kbs(user: User = Depends(get_current_user)):
    """List the knowledge bases visible to the caller's workspace."""
    return [
        kb for kb in _kbs.values() if kb["tenant_id"] == str(user.tenant_id)
    ]


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
async def get_kb(kb_id: str, user: User = Depends(get_current_user)):
    """Get knowledge base by ID"""
    kb = _get_scoped(kb_id, user)
    return kb


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
async def update_kb(
    kb_id: str,
    kb: KnowledgeBaseCreate,
    user: User = Depends(get_current_user),
):
    """Update knowledge base"""
    record = _get_scoped(kb_id, user)

    record.update({
        "name": kb.name,
        "description": kb.description,
        "slug": kb.slug or _slugify(kb.name),
        "settings": kb.settings,
        "updated_at": utcnow()
    })

    return record


@router.delete("/{kb_id}")
async def delete_kb(kb_id: str, user: User = Depends(get_current_user)):
    """Delete knowledge base"""
    _get_scoped(kb_id, user)

    del _kbs[kb_id]
    return {"message": "Knowledge base deleted"}


@router.post("/{kb_id}/publish")
async def publish_kb(kb_id: str, user: User = Depends(get_current_user)):
    """Publish knowledge base"""
    record = _get_scoped(kb_id, user)

    record["is_published"] = True
    record["status"] = "published"
    record["updated_at"] = utcnow()

    return {"message": "Knowledge base published", "kb_id": kb_id}


def _get_scoped(kb_id: str, user: User) -> dict:
    """Return the knowledge base only if it belongs to the caller's workspace."""
    record = _kbs.get(kb_id)
    if record is None or record["tenant_id"] != str(user.tenant_id):
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    return record