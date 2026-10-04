"""Billing API: membership plans, subscriptions and Stripe checkout."""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.utils.time import utcnow
from backend.app.dependencies import get_current_user, require_platform_user
from backend.app.models.billing import MembershipPlan, Subscription, SubscriptionStatus
from backend.app.models.user import User
from backend.app.schemas import (
    EntitlementResponse,
    MembershipPlanResponse,
    StripeCheckoutRequest,
    StripeCheckoutResponse,
    StripePortalRequest,
    StripePortalResponse,
    SubscriptionResponse,
    SubscriptionUpdate,
)
from backend.config import (
    MEMBERSHIP_PLANS,
    STRIPE_CANCEL_URL,
    STRIPE_SECRET_KEY,
    STRIPE_SUCCESS_URL,
    STRIPE_WEBHOOK_SECRET,
)
from backend.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


async def seed_default_plans(db: AsyncSession, tenant_id) -> None:
    """Ensure the tenant has one row per configured plan."""
    existing = await db.execute(
        select(MembershipPlan.code).where(MembershipPlan.tenant_id == tenant_id)
    )
    known = set(existing.scalars().all())

    for plan in MEMBERSHIP_PLANS:
        code = str(plan["code"])
        if code in known:
            continue
        db.add(
            MembershipPlan(
                tenant_id=tenant_id,
                code=code,
                stripe_price_id=plan.get("stripe_price_id"),
                stripe_product_id=plan.get("stripe_product_id"),
                name=str(plan.get("name", code)),
                description=plan.get("description"),
                price_cents=int(plan.get("price_cents", 0)),
                currency=str(plan.get("currency", "thb")),
                interval=str(plan.get("interval", "month")),
                api_calls_per_month=int(plan.get("api_calls_per_month", 0)),
                features=list(plan.get("features", [])),
                is_active=bool(plan.get("is_active", True)),
                sort_order=int(plan.get("sort_order", 0)),
            )
        )
    await db.flush()


def _stripe() -> object | None:
    if not STRIPE_SECRET_KEY:
        return None
    try:
        import stripe

        stripe.api_key = STRIPE_SECRET_KEY
        return stripe
    except Exception:
        logger.exception("Stripe SDK is unavailable")
        return None


async def _active_subscription(db: AsyncSession, user: User) -> Subscription | None:
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .where(Subscription.user_id == user.id)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    return result.scalars().first()


@router.get("/plans", response_model=List[MembershipPlanResponse])
async def list_plans(
    tenant_id: str | None = None,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    target = tenant_id or str(user.tenant_id)
    result = await db.execute(
        select(MembershipPlan)
        .where(MembershipPlan.tenant_id == target, MembershipPlan.is_active.is_(True))
        .order_by(MembershipPlan.sort_order)
    )
    return result.scalars().all()


@router.get("/subscription", response_model=SubscriptionResponse)
async def current_subscription(
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    subscription = await _active_subscription(db, user)
    if subscription is None:
        raise HTTPException(status_code=404, detail="No subscription found")
    return subscription


@router.patch("/subscription", response_model=SubscriptionResponse)
async def update_subscription(
    update: SubscriptionUpdate,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    subscription = await _active_subscription(db, user)
    if subscription is None:
        raise HTTPException(status_code=404, detail="No subscription found")
    if update.cancel_at_period_end is not None:
        subscription.cancel_at_period_end = update.cancel_at_period_end
        subscription.updated_at = utcnow()
        await db.commit()
        await db.refresh(subscription)
    return subscription


@router.get("/entitlements", response_model=EntitlementResponse)
async def entitlements(
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    subscription = await _active_subscription(db, user)
    if subscription is None or subscription.plan is None:
        return EntitlementResponse(
            plan="free",
            status=SubscriptionStatus.INCOMPLETE.value,
            api_calls_limit=0,
            features=[],
        )
    return EntitlementResponse(
        plan=subscription.plan.code,
        status=str(subscription.status),
        api_calls_limit=subscription.plan.api_calls_per_month,
        features=list(subscription.plan.features or []),
        current_period_end=subscription.current_period_end,
    )


@router.post("/checkout", response_model=StripeCheckoutResponse)
async def create_checkout(
    payload: StripeCheckoutRequest,
    request: Request,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    plan = await db.get(MembershipPlan, payload.plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")

    stripe = _stripe()
    if stripe is None:
        return StripeCheckoutResponse(
            message="Stripe is not configured on this deployment",
        )
    if plan.price_cents == 0:
        subscription = await _active_subscription(db, user)
        if subscription is None:
            subscription = Subscription(
                tenant_id=user.tenant_id,
                user_id=user.id,
                plan_id=plan.id,
                status=SubscriptionStatus.ACTIVE,
                current_period_start=utcnow(),
            )
            db.add(subscription)
            await db.commit()
        return StripeCheckoutResponse(message="Free plan applied without checkout")

    base_url = str(request.base_url).rstrip("/")
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=user.stripe_customer_id or None,
        client_reference_id=str(user.id),
        line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
        success_url=payload.success_url or STRIPE_SUCCESS_URL,
        cancel_url=payload.cancel_url or STRIPE_CANCEL_URL,
    )
    logger.info("Created Stripe checkout session %s for tenant %s", session.id, base_url)
    return StripeCheckoutResponse(checkout_url=session.url, session_id=session.id)


@router.post("/portal", response_model=StripePortalResponse)
async def create_portal(
    payload: StripePortalRequest,
    user: User = Depends(require_platform_user),
):
    stripe = _stripe()
    if stripe is None:
        raise HTTPException(status_code=503, detail="Stripe is not configured on this deployment")
    if not user.stripe_customer_id:
        raise HTTPException(status_code=400, detail="User has no Stripe customer")

    session = stripe.billing_portal.Session.create(
        customer=user.stripe_customer_id,
        return_url=payload.return_url or STRIPE_SUCCESS_URL,
    )
    return StripePortalResponse(portal_url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    stripe = _stripe()
    if stripe is None:
        raise HTTPException(status_code=503, detail="Stripe is not configured on this deployment")
    if not STRIPE_WEBHOOK_SECRET:
        # Verifying against an empty secret would reject every delivery, so fail
        # loudly instead of answering 200 to events nothing acted on.
        raise HTTPException(
            status_code=503, detail="STRIPE_WEBHOOK_SECRET is not configured on this deployment"
        )

    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, signature, STRIPE_WEBHOOK_SECRET)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=f"Invalid Stripe payload: {exc}") from exc

    if event["type"] in {"customer.subscription.created", "customer.subscription.updated"}:
        obj = event["data"]["object"]
        result = await db.execute(
            select(Subscription).where(Subscription.stripe_subscription_id == obj.get("id"))
        )
        subscription = result.scalar_one_or_none()
        if subscription is not None:
            subscription.status = obj.get("status", subscription.status)
            subscription.stripe_price_id = (obj.get("items", {}).get("data") or [{}])[0].get("price", {}).get("id")
            subscription.updated_at = utcnow()
            await db.commit()

    return {"received": True}


@router.post("/seed-plans", status_code=204)
async def seed_plans(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await seed_default_plans(db, user.tenant_id)
    await db.commit()