"""End-to-end check of the payment-gated signup.

Runs the real endpoint against a real database and a fake Stripe, so the
ordering guarantee is verified rather than assumed: a paid plan must not
create an account before the payment is confirmed.
"""
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from starlette.responses import Response as StarletteResponse

from backend.app.api import billing as billing_api
from backend.app.models.billing import (
    MembershipPlan,
    PendingRegistration,
    RegistrationStatus,
    Subscription,
    SubscriptionStatus,
)
from backend.app.models.tenant import Tenant
from backend.app.models.user import User
from backend.database import Base


class _FakeCheckoutSession:
    def __init__(self, id_: str, url: str):
        self.id = id_
        self.url = url


class _StripeSessionResource:
    """Mirrors `stripe.checkout.Session` — a class with `create`/`retrieve`."""

    def __init__(self, stripe: "_FakeStripe"):
        self._stripe = stripe

    def create(self, **kwargs):
        self._stripe.sessions_created.append(kwargs)
        return _FakeCheckoutSession("cs_test_1", "https://pay.test/cs_test_1")

    def retrieve(self, session_id):
        return {
            "id": session_id,
            "payment_status": "paid" if self._stripe.paid else "unpaid",
            "customer": "cus_test_1",
            "subscription": "sub_test_1",
        }


class _FakeStripeCheckout:
    def __init__(self, stripe: "_FakeStripe"):
        self.Session = _StripeSessionResource(stripe)


class _FakeStripe:
    """A Stripe stand-in that records what was asked of it."""

    def __init__(self):
        self.sessions_created: list[dict] = []
        self.paid = False
        self.checkout = _FakeStripeCheckout(self)


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    tables = [
        Tenant.__table__,
        User.__table__,
        MembershipPlan.__table__,
        Subscription.__table__,
        PendingRegistration.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=tables))
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        yield db
    await engine.dispose()


async def _seed(session):
    tenant = Tenant(id=uuid.uuid4(), name="Seed", slug="seed", is_active=True)
    session.add(tenant)
    session.add(
        MembershipPlan(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            code="free",
            name="Free",
            price_cents=0,
            features=[],
        )
    )
    session.add(
        MembershipPlan(
            id=uuid.uuid4(),
            tenant_id=tenant.id,
            code="pro",
            name="Pro",
            price_cents=29000,
            stripe_price_id="price_pro",
            features=[],
        )
    )
    await session.commit()
    return tenant


async def test_paid_signup_does_not_create_an_account_before_payment(session, monkeypatch):
    await _seed(session)
    stripe = _FakeStripe()
    monkeypatch.setattr(billing_api, "_stripe", lambda: stripe)

    payload = billing_api.SubscribeRequest(
        email="payer@example.com", password="longenough", plan_code="pro"
    )

    # The endpoint is a coroutine that also needs a Request and Response.
    class _Request:
        base_url = "http://test"

    class _Response(StarletteResponse):
        def __init__(self):
            super().__init__()

    response = _Response()
    result = await billing_api.subscribe(
        payload, _Request(), response, session
    )

    assert result.status == "checkout_created"
    assert result.checkout_url == "https://pay.test/cs_test_1"
    assert result.session_id == "cs_test_1"

    # A checkout session was created, but no account exists yet.
    assert len(stripe.sessions_created) == 1
    users = (await session.execute(select(User))).scalars().all()
    assert users == []

    # The signup is parked, waiting for the payment.
    pending = (await session.execute(select(PendingRegistration))).scalars().one()
    assert pending.status == RegistrationStatus.CHECKOUT_CREATED.value
    assert pending.plan_code == "pro"
    assert pending.stripe_checkout_session_id == "cs_test_1"


async def test_paid_signup_activates_once_stripe_confirms_the_payment(session, monkeypatch):
    await _seed(session)
    stripe = _FakeStripe()
    monkeypatch.setattr(billing_api, "_stripe", lambda: stripe)

    class _Request:
        base_url = "http://test"

    class _Response(StarletteResponse):
        def __init__(self):
            super().__init__()

    payload = billing_api.SubscribeRequest(
        email="payer@example.com", password="longenough", plan_code="pro"
    )
    await billing_api.subscribe(payload, _Request(), _Response(), session)

    # Stripe confirms the payment.
    stripe.paid = True
    status = await billing_api.subscribe_status(StarletteResponse(), "cs_test_1", session)

    assert status.activated is True
    assert status.status == "activated"

    # Now there is exactly one account, on the paid plan.
    users = (await session.execute(select(User))).scalars().all()
    assert len(users) == 1
    assert users[0].email == "payer@example.com"

    subscriptions = (await session.execute(select(Subscription))).scalars().all()
    assert len(subscriptions) == 1
    assert subscriptions[0].status == SubscriptionStatus.ACTIVE.value
    assert subscriptions[0].stripe_subscription_id == "sub_test_1"


async def test_free_signup_activates_without_a_payment(session, monkeypatch):
    await _seed(session)
    stripe = _FakeStripe()
    monkeypatch.setattr(billing_api, "_stripe", lambda: stripe)

    class _Request:
        base_url = "http://test"

    class _Response(StarletteResponse):
        def __init__(self):
            super().__init__()

    payload = billing_api.SubscribeRequest(
        email="free@example.com", password="longenough", plan_code="free"
    )
    result = await billing_api.subscribe(payload, _Request(), _Response(), session)

    assert result.status == "activated"
    assert result.access_token
    assert result.user is not None
    assert result.user.email == "free@example.com"

    # No checkout session was created and the account already exists.
    assert stripe.sessions_created == []
    users = (await session.execute(select(User))).scalars().all()
    assert len(users) == 1
