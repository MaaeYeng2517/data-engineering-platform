"""Administrative endpoints guarded by the admin role."""
import logging
from datetime import timedelta
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.utils.time import utcnow
from backend.app.dependencies import require_admin
from backend.app.models.api_key import ApiKey, ApiUsageLog
from backend.app.models.billing import MembershipPlan, Subscription, SubscriptionStatus
from backend.app.models.contact import ContactMessage, ContactStatus
from backend.app.models.tenant import Tenant
from backend.app.models.user import User, UserRole
from backend.app.schemas import (
    AdminStatsResponse,
    AdminTenantListResponse,
    AdminUserListResponse,
    ContactMessageResponse,
    ContactMessageUpdate,
    TenantResponse,
    UserResponse,
)
from backend.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


async def _count(db: AsyncSession, column, *conditions) -> int:
    result = await db.execute(select(func.count(column)).where(*conditions))
    return int(result.scalar() or 0)


@router.get("/stats", response_model=AdminStatsResponse)
async def platform_stats(
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    now = utcnow()
    month_start = now - timedelta(days=30)

    revenue = await db.execute(
        select(func.coalesce(func.sum(MembershipPlan.price_cents), 0))
        .select_from(Subscription)
        .join(MembershipPlan, Subscription.plan_id == MembershipPlan.id)
        .where(Subscription.status == SubscriptionStatus.ACTIVE.value)
    )

    return AdminStatsResponse(
        total_users=await _count(db, User.id),
        total_tenants=await _count(db, Tenant.id),
        total_subscriptions=await _count(db, Subscription.id),
        active_subscriptions=await _count(
            db, Subscription.id, Subscription.status == SubscriptionStatus.ACTIVE.value
        ),
        total_api_keys=await _count(db, ApiKey.id),
        active_api_keys=await _count(db, ApiKey.id, ApiKey.is_active.is_(True)),
        total_api_calls_today=await _count(
            db,
            ApiUsageLog.id,
            ApiUsageLog.created_at >= now.replace(hour=0, minute=0, second=0, microsecond=0),
        ),
        total_api_calls_month=await _count(db, ApiUsageLog.id, ApiUsageLog.created_at >= month_start),
        revenue_cents=int(revenue.scalar() or 0),
        contact_messages=await _count(db, ContactMessage.id),
        pending_contact_messages=await _count(
            db, ContactMessage.id, ContactMessage.status == ContactStatus.NEW.value
        ),
    )


@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total = await _count(db, User.id)
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return AdminUserListResponse(
        users=[UserResponse.model_validate(user) for user in result.scalars().all()],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    role: UserRole | None = None,
    is_active: bool | None = None,
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if role is not None:
        user.role = role
        user.is_superuser = role == UserRole.ADMIN
    if is_active is not None:
        user.is_active = is_active
    user.updated_at = utcnow()
    await db.commit()
    await db.refresh(user)
    return user


@router.get("/tenants", response_model=AdminTenantListResponse)
async def list_tenants(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    total = await _count(db, Tenant.id)
    result = await db.execute(
        select(Tenant)
        .order_by(Tenant.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return AdminTenantListResponse(
        tenants=[TenantResponse.model_validate(tenant) for tenant in result.scalars().all()],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/contact-messages", response_model=List[ContactMessageResponse])
async def list_contact_messages(
    message_status: ContactStatus | None = Query(None, alias="status"),
    _: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    query = select(ContactMessage).order_by(ContactMessage.created_at.desc())
    if message_status is not None:
        query = query.where(ContactMessage.status == message_status.value)
    result = await db.execute(query.limit(200))
    return result.scalars().all()


@router.patch("/contact-messages/{message_id}", response_model=ContactMessageResponse)
async def update_contact_message(
    message_id: str,
    update: ContactMessageUpdate,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    message = await db.get(ContactMessage, message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Contact message not found")

    if update.status is not None:
        message.status = update.status.value
        message.resolved_at = utcnow() if update.status == ContactStatus.RESOLVED else None
        message.resolved_by = admin.id if update.status == ContactStatus.RESOLVED else None
    if update.admin_notes is not None:
        message.admin_notes = update.admin_notes
    message.updated_at = utcnow()
    await db.commit()
    await db.refresh(message)
    return message