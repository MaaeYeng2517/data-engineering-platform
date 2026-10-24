"""Account activation shared by registration and the payment-gated signup.

Both entry points end in the same place: a tenant, an admin user, the
membership plans for that tenant and a subscription on the chosen plan. Keeping
that in one function means the free signup and the paid signup cannot drift
apart.
"""
import logging
import re
import uuid
from dataclasses import dataclass
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models.billing import MembershipPlan, Subscription, SubscriptionStatus
from backend.app.models.tenant import Tenant
from backend.app.models.user import User, UserRole
from backend.app.security import hash_password
from backend.app.utils.time import utcnow
from backend.config import ADMIN_EMAILS

logger = logging.getLogger(__name__)


@dataclass
class ActivatedAccount:
    user: User
    tenant: Tenant
    plan: MembershipPlan
    subscription: Subscription


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "member"


async def _unique_tenant_for_email(db: AsyncSession, email: str) -> Tenant:
    """Give every signup its own workspace.

    The slug is derived from the email local part, so two people with the same
    local part in different domains would collide — a random suffix is added
    until the slug is free.
    """
    local_part = email.split("@", 1)[0]
    base_slug = _slugify(local_part)
    for _ in range(100):
        slug = base_slug if _ == 0 else f"{base_slug}-{uuid.uuid4().hex[:8]}"
        result = await db.execute(select(Tenant.id).where(Tenant.slug == slug))
        if result.scalar_one_or_none() is None:
            tenant = Tenant(
                name=f"{local_part}'s workspace",
                slug=slug,
                description="Workspace created during membership registration",
                is_active=True,
            )
            db.add(tenant)
            await db.flush()
            return tenant
    raise HTTPException(status_code=503, detail="Unable to create workspace")


async def _seed_plans(db: AsyncSession, tenant_id) -> None:
    """Copy the configured plan catalogue onto the new tenant."""
    from backend.app.api.billing import seed_default_plans

    await seed_default_plans(db, tenant_id)


async def _plan_by_code(db: AsyncSession, tenant_id, code: str) -> MembershipPlan:
    result = await db.execute(
        select(MembershipPlan).where(
            MembershipPlan.tenant_id == tenant_id,
            MembershipPlan.code == code,
        )
    )
    plan = result.scalar_one_or_none()
    if plan is None:
        raise HTTPException(status_code=500, detail=f"Plan '{code}' is unavailable")
    return plan


async def activate_account(
    db: AsyncSession,
    *,
    email: str,
    password: Optional[str] = None,
    password_hash: Optional[str] = None,
    full_name: Optional[str] = None,
    plan_code: str = "free",
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None,
    stripe_price_id: Optional[str] = None,
    subscription_status: str = SubscriptionStatus.ACTIVE.value,
    data: Optional[dict] = None,
) -> ActivatedAccount:
    """Create the tenant, the admin user, the plans and the subscription.

    The password arrives either as plaintext (`password`) or already hashed
    (`password_hash`). The two are never mixed: hashing an existing hash would
    produce a password the user can never type. The paid signup stores the
    hash on the pending row and passes it back here, so the browser never has
    to resend the password after the payment.
    """
    if password is None and password_hash is None:
        raise ValueError("activate_account needs a password or a password_hash")

    email = email.strip().lower()

    existing = await db.execute(select(User.id).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    tenant = await _unique_tenant_for_email(db, email)
    role = UserRole.ADMIN if email in ADMIN_EMAILS else UserRole.MEMBER

    user = User(
        tenant_id=tenant.id,
        email=email,
        hashed_password=password_hash or hash_password(password),
        full_name=full_name.strip() if full_name else None,
        is_active=True,
        is_superuser=role == UserRole.ADMIN,
        role=role,
        stripe_customer_id=stripe_customer_id,
    )
    db.add(user)
    await db.flush()

    await _seed_plans(db, tenant.id)

    plan = await _plan_by_code(db, tenant.id, plan_code)
    subscription = Subscription(
        tenant_id=tenant.id,
        user_id=user.id,
        plan_id=plan.id,
        status=subscription_status,
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=stripe_subscription_id,
        stripe_price_id=stripe_price_id or plan.stripe_price_id,
        current_period_start=utcnow(),
        data=data or {},
    )
    db.add(subscription)

    await db.commit()
    await db.refresh(user)
    await db.refresh(plan)
    await db.refresh(subscription)

    logger.info(
        "Activated account %s on plan %s (subscription %s)",
        email,
        plan.code,
        subscription.stripe_subscription_id or "none",
    )
    return ActivatedAccount(
        user=user,
        tenant=tenant,
        plan=plan,
        subscription=subscription,
    )
