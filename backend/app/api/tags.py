"""Tag CRUD API endpoints."""
import logging
import re
import unicodedata
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import require_platform_user
from backend.app.models.tag import Tag
from backend.app.models.user import User
from backend.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode().lower()
    return _SLUG_STRIP.sub("-", ascii_only).strip("-") or "tag"


class TagCreate(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = "#6366f1"


class TagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class TagResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: Optional[str]
    color: str
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


async def _get_tag(db: AsyncSession, tag_id: UUID) -> Tag:
    tag = await db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


async def _unique_slug(db: AsyncSession, name: str, exclude_id: Optional[UUID] = None) -> str:
    base = _slugify(name)
    candidate = base
    suffix = 2
    while True:
        query = select(Tag.id).where(Tag.slug == candidate)
        if exclude_id is not None:
            query = query.where(Tag.id != exclude_id)
        if (await db.execute(query)).scalar_one_or_none() is None:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


@router.post("/tags", response_model=TagResponse, status_code=201)
async def create_tag(
    payload: TagCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_platform_user),
):
    """Create a new tag."""
    slug = await _unique_slug(db, payload.name)
    tag = Tag(
        name=payload.name,
        slug=slug,
        description=payload.description,
        color=payload.color,
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return _tag_response(tag)


@router.get("/tags", response_model=List[TagResponse])
async def list_tags(
    search: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_platform_user),
):
    """List all tags, optionally filtered by search."""
    query = select(Tag).order_by(Tag.name.asc()).limit(limit)
    if search:
        query = query.where(
            or_(
                Tag.name.ilike(f"%{search}%"),
                Tag.description.ilike(f"%{search}%"),
            )
        )
    result = await db.execute(query)
    tags = result.scalars().all()
    return [_tag_response(t) for t in tags]


@router.get("/tags/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_platform_user),
):
    """Get a tag by ID."""
    tag = await _get_tag(db, tag_id)
    return _tag_response(tag)


@router.put("/tags/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: UUID,
    payload: TagUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_platform_user),
):
    """Update a tag."""
    tag = await _get_tag(db, tag_id)
    data = payload.model_dump(exclude_unset=True)
    if "name" in data and data["name"]:
        data["slug"] = await _unique_slug(db, data["name"], exclude_id=tag_id)
    for field, value in data.items():
        setattr(tag, field, value)
    await db.commit()
    await db.refresh(tag)
    return _tag_response(tag)


@router.delete("/tags/{tag_id}")
async def delete_tag(
    tag_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_platform_user),
):
    """Delete a tag."""
    tag = await _get_tag(db, tag_id)
    await db.delete(tag)
    await db.commit()
    return {"message": "Tag deleted"}


def _tag_response(tag: Tag) -> TagResponse:
    return TagResponse(
        id=str(tag.id),
        name=tag.name,
        slug=tag.slug,
        description=tag.description,
        color=tag.color,
        created_at=tag.created_at.isoformat() if tag.created_at else None,
        updated_at=tag.updated_at.isoformat() if tag.updated_at else None,
    )