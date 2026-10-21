"""Billing API: membership plans, subscriptions, Stripe checkout and paid signup."""
import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.utils.time import utcnow
from backend.app.dependencies import get_current_user, require_platform_user
from backend.app.models.billing import (
    MembershipPlan,
    PendingRegistration,
    RegistrationStatus,
    Subscription,
    SubscriptionStatus,
)
from backend.app.models.user import User
from backend.app.schemas import (
    EntitlementResponse,
    MembershipPlanResponse,
    PublicPlanResponse,
    StripeCheckoutRequest,
    StripeCheckoutResponse,
    StripePortalRequest,
    StripePortalResponse,
    SubscribeRequest,
    SubscribeResponse,
    SubscribeStatusResponse,
    SubscriptionResponse,
    SubscriptionUpdate,
    UserResponse,
)
from backend.app.security import create_csrf_token, hash_password, set_auth_cookies
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


def _token_pair(user: User) -> tuple[str, str, str]:
    """Build the access/refresh/CSRF triple for a freshly activated user."""
    from backend.app.security import create_access_token, create_refresh_token

    payload = {
        "user_id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "role": user.role.value,
    }
    return create_access_token(payload), create_refresh_token(payload), create_csrf_token()


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


async def _pending_by_email(db: AsyncSession, email: str) -> PendingRegistration | None:
    result = await db.execute(
        select(PendingRegistration).where(PendingRegistration.email == email)
    )
    return result.scalar_one_or_none()


async def _pending_by_session(
    db: AsyncSession, session_id: str
) -> PendingRegistration | None:
    result = await db.execute(
        select(PendingRegistration).where(
            PendingRegistration.stripe_checkout_session_id == session_id
        )
    )
    return result.scalar_one_or_none()


def _configured_plan(code: str) -> dict | None:
    """The authoritative plan definition from the environment."""
    from backend.config import MEMBERSHIP_PLANS

    for plan in MEMBERSHIP_PLANS:
        if str(plan.get("code")) == code:
            return plan
    return None


async def _plan_by_code(db: AsyncSession, code: str) -> MembershipPlan | None:
    """Find a plan in any tenant — used before the tenant exists.

    Every tenant holds its own copy of the catalogue, and a copy created before
    a price change keeps the old price. The configured catalogue is therefore
    authoritative for the amount and the Stripe price. A transient object is
    returned so the stored row is never mutated as a side effect of a lookup.
    """
    result = await db.execute(
        select(MembershipPlan)
        .where(MembershipPlan.code == code, MembershipPlan.is_active.is_(True))
        .order_by(MembershipPlan.sort_order)
        .limit(1)
    )
    stored = result.scalar_one_or_none()

    config = _configured_plan(code)
    if config is None:
        return stored

    stored_price_id = stored.stripe_price_id if stored is not None else None
    return MembershipPlan(
        id=stored.id if stored is not None else uuid.uuid4(),
        tenant_id=stored.tenant_id if stored is not None else uuid.uuid4(),
        code=code,
        name=str(config.get("name", code)),
        description=config.get("description"),
        price_cents=int(
            config["price_cents"] if "price_cents" in config
            else (stored.price_cents if stored is not None else 0)
        ),
        currency=str(config.get("currency", "thb")),
        interval=str(config.get("interval", "month")),
        api_calls_per_month=int(config.get("api_calls_per_month", 0)),
        stripe_price_id=config.get("stripe_price_id") or stored_price_id,
        features=list(config.get("features", [])),
        is_active=bool(config.get("is_active", True)),
        sort_order=int(config.get("sort_order", 0)),
    )


async def _activate_pending(
    db: AsyncSession,
    pending: PendingRegistration,
    *,
    stripe_customer_id: str | None = None,
    stripe_subscription_id: str | None = None,
) -> bool:
    """Turn a paid registration into a real account. Idempotent.

    Returns True when the account exists afterwards. The password is already
    hashed on the pending row, so it is restored rather than re-hashed.
    """
    if pending.status == RegistrationStatus.COMPLETED.value:
        return True

    from backend.app.services.onboarding import activate_account

    try:
        activated = await activate_account(
            db,
            email=pending.email,
            password=pending.password_hash,
            full_name=pending.full_name,
            plan_code=pending.plan_code,
            stripe_customer_id=stripe_customer_id or pending.stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            data={"source": "paid_signup", "pending_registration_id": str(pending.id)},
        )
    except HTTPException as exc:
        if exc.status_code == 409:
            # The account already exists — a duplicate webhook delivery.
            pending.status = RegistrationStatus.COMPLETED.value
            pending.completed_at = utcnow()
            await db.commit()
            return True
        pending.status = RegistrationStatus.FAILED.value
        pending.failure_reason = str(exc.detail)
        await db.commit()
        raise

    pending.status = RegistrationStatus.COMPLETED.value
    pending.completed_at = utcnow()
    pending.created_user_id = activated.user.id
    if stripe_subscription_id:
        pending.stripe_subscription_id = stripe_subscription_id
    if stripe_customer_id:
        pending.stripe_customer_id = stripe_customer_id
    await db.commit()
    return True


@router.post("/subscribe", response_model=SubscribeResponse)
async def subscribe(
    payload: SubscribeRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Start a signup that only activates after the payment settles.

    The free plan activates immediately. Every paid plan creates a Stripe
    Checkout session and returns its URL — the account is created by the
    webhook (or by the status poll) once Stripe confirms the payment.
    """

    email = payload.email.strip().lower()

    existing_user = await db.execute(select(User.id).where(User.email == email))
    if existing_user.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    plan = await _plan_by_code(db, payload.plan_code)
    if plan is None:
        raise HTTPException(status_code=404, detail=f"Plan '{payload.plan_code}' not found")

    pending = await _pending_by_email(db, email)
    if pending is not None and pending.status in {
        RegistrationStatus.PENDING.value,
        RegistrationStatus.CHECKOUT_CREATED.value,
    }:
        # A previous attempt for the same email: reuse it rather than
        # creating a second checkout session.
        if pending.plan_code != plan.code:
            raise HTTPException(
                status_code=409,
                detail="An unfinished checkout already exists for this email",
            )
    else:
        pending = PendingRegistration(
            email=email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name.strip() if payload.full_name else None,
            plan_code=plan.code,
            amount_cents=plan.price_cents,
            currency=plan.currency,
            status=RegistrationStatus.PENDING.value,
        )
        db.add(pending)
        await db.flush()

    if plan.price_cents == 0:
        from backend.app.services.onboarding import activate_account

        activated = await activate_account(
            db,
            email=email,
            password=payload.password,
            full_name=payload.full_name,
            plan_code=plan.code,
            data={"source": "free_signup"},
        )
        pending.status = RegistrationStatus.COMPLETED.value
        pending.completed_at = utcnow()
        pending.created_user_id = activated.user.id
        await db.commit()

        access_token, refresh_token, csrf_token = _token_pair(activated.user)
        set_auth_cookies(response, access_token, refresh_token, csrf_token)
        return SubscribeResponse(
            status="activated",
            message="Your workspace is ready",
            plan_code=plan.code,
            amount_cents=0,
            currency=plan.currency,
            access_token=access_token,
            user=UserResponse.model_validate(activated.user),
            csrf_token=csrf_token,
        )

    stripe = _stripe()
    if stripe is None:
        raise HTTPException(
            status_code=503,
            detail="Payments are not configured on this deployment",
        )
    if not plan.stripe_price_id:
        raise HTTPException(
            status_code=503,
            detail=f"Plan '{plan.code}' has no configured price",
        )

    base_url = str(request.base_url).rstrip("/")
    session = stripe.checkout.Session.create(
        mode="subscription",
        customer=pending.stripe_customer_id or None,
        client_reference_id=str(pending.id),
        customer_email=email if not pending.stripe_customer_id else None,
        line_items=[{"price": plan.stripe_price_id, "quantity": 1}],
        success_url=payload.success_url or STRIPE_SUCCESS_URL,
        cancel_url=payload.cancel_url or STRIPE_CANCEL_URL,
        metadata={"pending_registration_id": str(pending.id), "plan_code": plan.code},
        subscription_data={"metadata": {"pending_registration_id": str(pending.id)}},
    )
    pending.status = RegistrationStatus.CHECKOUT_CREATED.value
    pending.stripe_checkout_session_id = session.id
    try:
        await db.commit()
    except IntegrityError:
        # A checkout session id is unique, and so is the email. A collision
        # means the same signup was submitted twice concurrently.
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A checkout is already in progress for this email",
        ) from None

    logger.info(
        "Created checkout session %s for %s on plan %s (%s)",
        session.id,
        email,
        plan.code,
        base_url,
    )
    return SubscribeResponse(
        status="checkout_created",
        message="Complete the payment to activate the workspace",
        checkout_url=session.url,
        session_id=session.id,
        plan_code=plan.code,
        amount_cents=plan.price_cents,
        currency=plan.currency,
    )


@router.get("/subscribe/status", response_model=SubscribeStatusResponse)
async def subscribe_status(
    session_id: str = Query(..., min_length=4, max_length=255),
    db: AsyncSession = Depends(get_db),
):
    """Report whether the paid signup has become a usable account.

    The webhook is the primary path. This endpoint asks Stripe directly as a
    fallback, so a delayed or missed webhook still unblocks the user.
    """
    pending = await _pending_by_session(db, session_id)
    if pending is None:
        raise HTTPException(status_code=404, detail="Checkout session not found")

    if pending.status == RegistrationStatus.COMPLETED.value:
        return SubscribeStatusResponse(
            status="activated",
            activated=True,
            plan_code=pending.plan_code,
            email=pending.email,
            message="Your workspace is ready",
        )

    if pending.status == RegistrationStatus.FAILED.value:
        return SubscribeStatusResponse(
            status="failed",
            activated=False,
            plan_code=pending.plan_code,
            email=pending.email,
            message=pending.failure_reason or "The payment could not be applied",
        )

    stripe = _stripe()
    if stripe is not None:
        try:
            session = stripe.checkout.Session.retrieve(session_id)
        except Exception:
            logger.exception("Could not retrieve Stripe checkout session %s", session_id)
            session = None

        if session is not None and session.get("payment_status") in {"paid", "no_payment_required"}:
            await _activate_pending(
                db,
                pending,
                stripe_customer_id=session.get("customer"),
                stripe_subscription_id=session.get("subscription"),
            )
            return SubscribeStatusResponse(
                status="activated",
                activated=True,
                plan_code=pending.plan_code,
                email=pending.email,
                message="Your workspace is ready",
            )

    return SubscribeStatusResponse(
        status=pending.status,
        activated=False,
        plan_code=pending.plan_code,
        email=pending.email,
        message="Waiting for the payment to be confirmed",
    )


async def _active_subscription(db: AsyncSession, user: User) -> Subscription | None:
    result = await db.execute(
        select(Subscription)
        .options(selectinload(Subscription.plan))
        .where(Subscription.user_id == user.id)
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    return result.scalars().first()


@router.get("/public-plans", response_model=List[PublicPlanResponse])
async def public_plans(db: AsyncSession = Depends(get_db)):
    """The plan catalogue, readable without an account.

    A visitor picks a plan before they have one, so the pricing page cannot
    depend on an authenticated request.
    """
    from backend.config import MEMBERSHIP_PLANS

    # Every tenant holds its own copy of the catalogue, so the same code
    # appears once per tenant and a copy made before a price change keeps the
    # old price. The configured catalogue is authoritative.
    result = await db.execute(
        select(MembershipPlan)
        .where(MembershipPlan.is_active.is_(True))
        .order_by(MembershipPlan.sort_order)
    )
    unique: dict[str, MembershipPlan] = {}
    for plan in result.scalars().all():
        unique.setdefault(plan.code, plan)

    def _to_public(code: str, fallback: MembershipPlan | None) -> PublicPlanResponse:
        config = _configured_plan(code)
        if config is None:
            if fallback is None:
                raise HTTPException(status_code=404, detail=f"Plan '{code}' not found")
            return PublicPlanResponse(
                code=fallback.code,
                name=fallback.name,
                description=fallback.description,
                price_cents=fallback.price_cents,
                currency=fallback.currency,
                interval=fallback.interval,
                api_calls_per_month=fallback.api_calls_per_month,
                features=list(fallback.features or []),
                requires_payment=fallback.price_cents > 0,
            )
        price_cents = int(
            config["price_cents"] if "price_cents" in config
            else (fallback.price_cents if fallback is not None else 0)
        )
        return PublicPlanResponse(
            code=code,
            name=str(config.get("name", code)),
            description=config.get("description"),
            price_cents=price_cents,
            currency=str(config.get("currency", "thb")),
            interval=str(config.get("interval", "month")),
            api_calls_per_month=int(config.get("api_calls_per_month", 0)),
            features=list(config.get("features", [])),
            requires_payment=price_cents > 0,
        )

    if unique:
        return [
            _to_public(code, plan)
            for code, plan in sorted(unique.items(), key=lambda item: item[1].sort_order)
        ]

    # No tenant has been created yet — fall back to the configured catalogue.
    return [
        PublicPlanResponse(
            code=str(plan["code"]),
            name=str(plan.get("name", plan["code"])),
            description=plan.get("description"),
            price_cents=int(plan.get("price_cents", 0)),
            currency=str(plan.get("currency", "thb")),
            interval=str(plan.get("interval", "month")),
            api_calls_per_month=int(plan.get("api_calls_per_month", 0)),
            features=list(plan.get("features", [])),
            requires_payment=int(plan.get("price_cents", 0)) > 0,
        )
        for plan in MEMBERSHIP_PLANS
    ]


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

    if event["type"] == "checkout.session.completed":
        obj = event["data"]["object"]
        session_id = obj.get("id")
        pending_id = (obj.get("metadata") or {}).get("pending_registration_id")
        pending = None
        if session_id:
            pending = await _pending_by_session(db, session_id)
        if pending is None and pending_id:
            result = await db.execute(
                select(PendingRegistration).where(PendingRegistration.id == pending_id)
            )
            pending = result.scalar_one_or_none()
        if pending is not None:
            await _activate_pending(
                db,
                pending,
                stripe_customer_id=obj.get("customer"),
                stripe_subscription_id=obj.get("subscription"),
            )

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