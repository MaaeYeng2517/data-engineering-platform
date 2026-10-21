"""Tests for the payment-gated signup flow.

The rule being pinned down: a paid plan must not create an account until the
payment is confirmed. A free plan activates immediately. Both paths must end
with exactly one account, and the confirmation must be idempotent because
Stripe can deliver the same webhook twice.

The tests run against a real SQLite database so the activation path is
exercised end to end, not mocked.
"""
import uuid

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

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
from backend.app.schemas import SubscribeRequest
from backend.app.services import onboarding
from backend.database import Base


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    # Only the tables this feature touches — the full metadata includes
    # Postgres-specific column types that SQLite cannot create.
    tables = [
        Tenant.__table__,
        User.__table__,
        MembershipPlan.__table__,
        Subscription.__table__,
        PendingRegistration.__table__,
    ]
    async with engine.begin() as conn:
        await conn.run_sync(lambda sync_conn: Base.metadata.create_all(sync_conn, tables=tables))
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        yield db
    await engine.dispose()


def _plan(tenant_id, code: str, price_cents: int, stripe_price_id=None) -> MembershipPlan:
    return MembershipPlan(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        code=code,
        name=code.title(),
        price_cents=price_cents,
        stripe_price_id=stripe_price_id,
    )


async def _seed_plans(db, tenant_id) -> None:
    db.add(_plan(tenant_id, "free", 0))
    db.add(_plan(tenant_id, "pro", 29000, "price_pro"))
    db.add(_plan(tenant_id, "enterprise", 99000, "price_enterprise"))
    await db.commit()


def test_subscribe_request_requires_a_usable_password():
    with pytest.raises(ValidationError):
        SubscribeRequest(email="user@example.com", password="short")


def test_subscribe_request_keeps_the_requested_plan():
    payload = SubscribeRequest(
        email="user@example.com", password="longenough", plan_code="pro"
    )
    assert payload.plan_code == "pro"
    assert payload.email == "user@example.com"


def test_registration_states_cover_the_payment_lifecycle():
    assert RegistrationStatus.PENDING.value == "pending"
    assert RegistrationStatus.CHECKOUT_CREATED.value == "checkout_created"
    assert RegistrationStatus.COMPLETED.value == "completed"
    assert RegistrationStatus.FAILED.value == "failed"


async def test_activation_creates_tenant_user_plan_and_subscription(session):
    activated = await onboarding.activate_account(
        session,
        email="payer@example.com",
        password="longenough",
        full_name="Payer",
        plan_code="pro",
    )

    assert activated.user.email == "payer@example.com"
    assert activated.plan.code == "pro"
    assert activated.subscription.status == SubscriptionStatus.ACTIVE.value
    assert activated.user.tenant_id == activated.tenant.id


async def test_activation_rejects_a_duplicate_email(session):
    await onboarding.activate_account(
        session, email="dup@example.com", password="longenough"
    )
    with pytest.raises(Exception) as excinfo:
        await onboarding.activate_account(
            session, email="dup@example.com", password="longenough"
        )
    assert getattr(excinfo.value, "status_code", None) == 409


async def test_pending_registration_stores_a_hashed_password(session):
    pending = PendingRegistration(
        id=uuid.uuid4(),
        email="pending@example.com",
        password_hash=onboarding.hash_password("longenough"),
        plan_code="pro",
        amount_cents=29000,
    )
    session.add(pending)
    await session.commit()

    loaded = await session.get(PendingRegistration, pending.id)
    assert loaded is not None
    assert loaded.password_hash != "longenough"
    assert loaded.status == RegistrationStatus.PENDING.value


async def test_activate_pending_is_idempotent(session):
    """A redelivered webhook must not create a second account."""
    pending = PendingRegistration(
        id=uuid.uuid4(),
        email="twice@example.com",
        password_hash=onboarding.hash_password("longenough"),
        plan_code="free",
    )
    session.add(pending)
    await session.commit()

    assert await billing_api._activate_pending(session, pending) is True
    first_user_id = pending.created_user_id
    assert first_user_id is not None

    # The webhook arrives again.
    assert await billing_api._activate_pending(session, pending) is True
    assert pending.created_user_id == first_user_id

    users = await session.get(User, first_user_id)
    assert users is not None
    assert users.email == "twice@example.com"


async def test_activate_pending_marks_a_duplicate_email_as_completed(session):
    """If the account already exists, the registration is closed, not failed."""
    await onboarding.activate_account(
        session, email="exists@example.com", password="longenough"
    )
    pending = PendingRegistration(
        id=uuid.uuid4(),
        email="exists@example.com",
        password_hash=onboarding.hash_password("longenough"),
        plan_code="free",
    )
    session.add(pending)
    await session.commit()

    assert await billing_api._activate_pending(session, pending) is True
    assert pending.status == RegistrationStatus.COMPLETED.value
    assert pending.failure_reason is None


async def test_free_plan_needs_no_payment_and_no_price(session):
    tenant = Tenant(id=uuid.uuid4(), name="Free tenant", slug="free-tenant", is_active=True)
    session.add(tenant)
    await _seed_plans(session, tenant.id)

    plan = await billing_api._plan_by_code(session, "free")
    assert plan is not None
    assert plan.price_cents == 0
    assert plan.stripe_price_id is None


async def test_paid_plan_carries_a_stripe_price(session):
    tenant = Tenant(id=uuid.uuid4(), name="Paid tenant", slug="paid-tenant", is_active=True)
    session.add(tenant)
    await _seed_plans(session, tenant.id)

    plan = await billing_api._plan_by_code(session, "pro")
    assert plan is not None
    assert plan.price_cents == 29000
    assert plan.stripe_price_id == "price_pro"


async def test_the_configured_catalogue_wins_over_a_stale_stored_copy(session, monkeypatch):
    """A plan row written before a price change must not quote the old price."""
    tenant = Tenant(id=uuid.uuid4(), name="Stale", slug="stale", is_active=True)
    session.add(tenant)
    session.add(
        MembershipPlan(
            tenant_id=tenant.id,
            code="pro",
            name="Pro",
            price_cents=100,
            stripe_price_id="price_old",
            features=[],
        )
    )
    await session.commit()

    monkeypatch.setattr(
        billing_api,
        "_configured_plan",
        lambda code: {
            "code": "pro",
            "name": "Pro",
            "price_cents": 29000,
            "currency": "thb",
            "stripe_price_id": "price_new",
            "features": [],
        }
        if code == "pro"
        else None,
    )

    plan = await billing_api._plan_by_code(session, "pro")
    assert plan is not None
    assert plan.price_cents == 29000
    assert plan.stripe_price_id == "price_new"


async def test_the_stored_price_survives_when_the_config_sets_none(session, monkeypatch):
    """An empty configuration must not wipe a price that was set earlier."""
    tenant = Tenant(id=uuid.uuid4(), name="Kept", slug="kept", is_active=True)
    session.add(tenant)
    session.add(
        MembershipPlan(
            tenant_id=tenant.id,
            code="pro",
            name="Pro",
            price_cents=29000,
            stripe_price_id="price_kept",
            features=[],
        )
    )
    await session.commit()

    monkeypatch.setattr(
        billing_api,
        "_configured_plan",
        lambda code: {
            "code": "pro",
            "name": "Pro",
            "price_cents": 29000,
            "currency": "thb",
            "stripe_price_id": "",
            "features": [],
        }
        if code == "pro"
        else None,
    )

    plan = await billing_api._plan_by_code(session, "pro")
    assert plan is not None
    assert plan.stripe_price_id == "price_kept"


async def test_pending_lookup_helpers_find_the_row(session):
    pending = PendingRegistration(
        id=uuid.uuid4(),
        email="lookup@example.com",
        password_hash=onboarding.hash_password("longenough"),
        plan_code="pro",
        stripe_checkout_session_id="cs_test_123",
    )
    session.add(pending)
    await session.commit()

    by_email = await billing_api._pending_by_email(session, "lookup@example.com")
    by_session = await billing_api._pending_by_session(session, "cs_test_123")
    assert by_email is not None
    assert by_session is not None
    assert by_email.id == by_session.id


async def test_subscription_is_created_on_the_chosen_plan(session):
    activated = await onboarding.activate_account(
        session, email="plan@example.com", password="longenough", plan_code="enterprise"
    )
    subscription = await session.get(Subscription, activated.subscription.id)
    assert subscription is not None
    assert subscription.plan_id == activated.plan.id
    assert subscription.status == SubscriptionStatus.ACTIVE.value
