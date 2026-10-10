"""Tests for application startup wiring and the CSRF middleware.

The lifespan and the CSRF exemptions are the two pieces of `backend.main` that
nothing else exercises, and both fail silently when they break: a lifespan that
never runs leaves an unmigrated database, and a missing CSRF exemption turns
every marketing-page chat request into a 403. `init_db` and the session factory
are patched so the suite stays hermetic.
"""
import httpx
import pytest

import backend.main as main_module
from backend.main import app


def _rows(*rows):
    class _Result:
        def scalars(self):
            return self

        def all(self):
            return list(rows)

    return _Result()


class _Session:
    def __init__(self, *tenants):
        self._tenants = tenants
        self.executed = 0

    async def execute(self, *args, **kwargs):
        self.executed += 1
        return _rows(*self._tenants)

    async def commit(self):
        return None


class _SessionContext:
    def __init__(self, session):
        self._session = session

    async def __aenter__(self):
        return self._session

    async def __aexit__(self, *args):
        return False


@pytest.fixture
def startup_calls(monkeypatch):
    """Patch every side effect the startup hook performs."""
    calls = {"init_db": 0, "validate": 0, "rehydrate": 0}
    session = _Session()
    monkeypatch.setattr(session, "executed", session.executed)

    async def fake_init_db():
        calls["init_db"] += 1

    def fake_validate():
        calls["validate"] += 1

    async def fake_rehydrate(db):
        calls["rehydrate"] += 1
        return 0

    monkeypatch.setattr(main_module, "init_db", fake_init_db)
    monkeypatch.setattr(main_module, "validate_production_config", fake_validate)
    monkeypatch.setattr(main_module, "rehydrate_index", fake_rehydrate)
    monkeypatch.setattr(main_module, "async_session_factory", lambda: _SessionContext(session))
    return calls, session


async def run_lifespan():
    async with app.router.lifespan_context(app):
        pass


async def test_lifespan_initialises_the_database(startup_calls):
    calls, session = startup_calls

    await run_lifespan()

    assert calls["init_db"] == 1
    assert calls["validate"] == 1
    # The search index is per-process state, so it is rebuilt from the stored
    # chunks on every start.
    assert calls["rehydrate"] == 1
    # Active tenants are enumerated so their default plans can be seeded.
    assert session.executed == 1


async def test_lifespan_seeds_default_plans_per_active_tenant(monkeypatch, startup_calls):
    tenants = [
        type("Tenant", (), {"id": "tenant-1"})(),
        type("Tenant", (), {"id": "tenant-2"})(),
    ]
    monkeypatch.setattr(
        main_module, "async_session_factory", lambda: _SessionContext(_Session(*tenants))
    )
    seeded: list[str] = []

    import backend.app.api.billing as billing

    async def fake_seed(db, tenant_id):
        seeded.append(tenant_id)

    monkeypatch.setattr(billing, "seed_default_plans", fake_seed)

    await run_lifespan()

    assert seeded == ["tenant-1", "tenant-2"]


def client() -> httpx.AsyncClient:
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://test")


async def test_root_reports_the_running_service():
    async with client() as async_client:
        response = await async_client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "running"
        assert "timestamp" in response.json()


async def test_health_degrades_to_503_without_a_database(monkeypatch):
    class _UnavailableSessionContext:
        async def __aenter__(self):
            raise RuntimeError("connection refused")

        async def __aexit__(self, *args):
            return False

    monkeypatch.setattr(
        main_module, "async_session_factory", lambda: _UnavailableSessionContext()
    )

    async with client() as async_client:
        response = await async_client.get("/health")
        assert response.status_code == 503
        assert response.json()["detail"] == "Database unavailable"


async def test_health_reports_healthy_with_a_database(monkeypatch):
    monkeypatch.setattr(main_module, "async_session_factory", lambda: _SessionContext(_Session()))

    async with client() as async_client:
        response = await async_client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


async def test_chat_is_exempt_from_csrf_but_other_posts_are_not():
    async with client() as async_client:
        # An empty body still fails validation, but never on CSRF.
        chat = await async_client.post("/api/v1/chat", json={})
        assert chat.status_code != 403

        protected = await async_client.post("/api/v1/knowledge-bases", json={})
        assert protected.status_code == 403
        assert "CSRF" in protected.json()["detail"]


async def test_api_key_and_bearer_requests_bypass_csrf():
    async with client() as async_client:
        with_key = await async_client.post("/api/v1/knowledge-bases", json={}, headers={"x-api-key": "k"})
        assert with_key.status_code != 403

        with_bearer = await async_client.post(
            "/api/v1/knowledge-bases", json={}, headers={"authorization": "Bearer token"}
        )
        assert with_bearer.status_code != 403


def test_public_routes_are_registered():
    paths = {route.path for route in app.routes}
    assert "/health" in paths
    assert "/api/v1/chat/providers" in paths
    assert "/api/v1/chat/stream" in paths
