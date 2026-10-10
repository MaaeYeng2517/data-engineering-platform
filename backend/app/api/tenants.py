"""Tenants API endpoints.

A tenant is the isolation boundary for everything else, so this router is the
one place that decides who may see or change a workspace: platform admins see
all of them, everyone else sees only the workspace they belong to.
"""
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.dependencies import get_current_user, require_admin
from backend.app.models.tenant import Tenant
from backend.app.models.user import User
from backend.app.schemas import TenantCreate, TenantResponse
from backend.database import get_db

router = APIRouter()


async def _get_scoped(db: AsyncSession, tenant_id: UUID, user: User) -> Tenant:
    """Load a tenant the caller is allowed to see.

    Admins may load any tenant; everyone else only their own. A tenant that
    does not exist and a tenant owned by someone else both return 404, so ids
    cannot be probed across workspaces.
    """
    query = select(Tenant).where(Tenant.id == tenant_id)
    if not (user.role == "admin" or user.is_superuser):
        query = query.where(Tenant.id == user.tenant_id)

    record = (await db.execute(query)).scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return record


@router.post("/", response_model=TenantResponse)
async def create_tenant(
    tenant: TenantCreate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tenant (platform admin only)"""
    existing = await db.execute(
        select(func.count()).select_from(Tenant).where(
            (Tenant.slug == tenant.slug) | (Tenant.name == tenant.name)
        )
    )
    if existing.scalar_one():
        raise HTTPException(status_code=409, detail="That tenant name or slug is taken")

    record = Tenant(
        name=tenant.name,
        slug=tenant.slug,
        description=tenant.description,
        settings=tenant.settings or {},
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List tenants: all of them for an admin, otherwise just the caller's own."""
    query = select(Tenant)
    if not (user.role == "admin" or user.is_superuser):
        query = query.where(Tenant.id == user.tenant_id)

    result = await db.execute(query.order_by(Tenant.created_at.desc()))
    return list(result.scalars().all())


@router.get("/current", response_model=TenantResponse)
async def current_tenant(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The workspace the caller belongs to."""
    return await _get_scoped(db, user.tenant_id, user)


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get tenant by ID"""
    return await _get_scoped(db, tenant_id, user)


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: UUID,
    tenant: TenantCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update tenant"""
    record = await _get_scoped(db, tenant_id, user)

    record.name = tenant.name
    record.description = tenant.description
    record.settings = tenant.settings or {}
    if tenant.slug and tenant.slug != record.slug:
        clash = await db.execute(
            select(func.count()).select_from(Tenant).where(
                (Tenant.slug == tenant.slug) & (Tenant.id != record.id)
            )
        )
        if clash.scalar_one():
            raise HTTPException(status_code=409, detail="That slug is taken")
        record.slug = tenant.slug

    await db.commit()
    await db.refresh(record)
    return record


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: UUID,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Delete a tenant and everything inside it (platform admin only)"""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Tenant not found")

    await db.delete(record)
    await db.commit()
    return {"message": "Tenant deleted"}