"""Main FastAPI application."""
import logging
import time
from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from sqlalchemy import select

from backend.app.utils.time import utcnow
from backend.app.api import (
    admin,
    api_keys,
    auth,
    billing,
    chat,
    connectors,
    contact,
    documents,
    evaluation,
    governance,
    knowledge_bases,
    metadata,
    platform,
    profiles,
    rag,
    search,
    system,
    tenants,
    work_groups,
    workflows,
)
from backend.app.dependencies import require_platform_user
from backend.app.models.api_key import ApiUsageLog
from backend.app.observability import configure_telemetry, shutdown_telemetry
from backend.app.security import CSRF_COOKIE_NAME, verify_csrf_token
from backend.app.services.indexing.pipeline import rehydrate_index
from backend.config import (
    ALLOWED_ORIGINS,
    APP_NAME,
    APP_VERSION,
    validate_production_config,
)
from backend.database import async_session_factory, engine, init_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with async_session_factory() as db:
        await init_db()
        # The search index is per-process state; rebuild it from the stored
        # chunks so a restart does not serve an empty index.
        indexed = await rehydrate_index(db)

    validate_production_config()

    from backend.app.api.billing import seed_default_plans
    from backend.app.models.tenant import Tenant

    async with async_session_factory() as db:
        tenants = (await db.execute(select(Tenant).where(Tenant.is_active.is_(True)))).scalars().all()
        for tenant in tenants:
            await seed_default_plans(db, tenant.id)
    logger.info("Database initialized, %d chunks rehydrated into the index", indexed)
    try:
        yield
    finally:
        shutdown_telemetry()


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Knowledge Engineering Platform API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Installed at import time: the FastAPI instrumentation adds middleware, which
# Starlette refuses once the application has started.
configure_telemetry(app, engine=engine)


@app.middleware("http")
async def api_usage_middleware(request: Request, call_next):
    """Record one usage row per API-key request.

    Only key-authenticated calls are logged: browser sessions are already
    visible in the access logs, and logging every page view would drown the
    per-key usage the `/api-keys/usage` endpoints report.
    """
    started = time.perf_counter()
    response = await call_next(request)

    api_key_id = getattr(request.state, "api_key_id", None)
    user_id = getattr(request.state, "user_id", None)
    if api_key_id and user_id:
        try:
            async with async_session_factory() as db:
                db.add(
                    ApiUsageLog(
                        api_key_id=UUID(api_key_id),
                        user_id=UUID(user_id),
                        tenant_id=UUID(request.state.tenant_id),
                        endpoint=request.url.path,
                        method=request.method,
                        status_code=response.status_code,
                        latency_ms=int((time.perf_counter() - started) * 1000),
                        ip_address=request.client.host if request.client else None,
                        user_agent=request.headers.get("user-agent"),
                    )
                )
                await db.commit()
        except Exception as exc:  # pragma: no cover - logging must not fail a request
            logger.warning("Could not record API usage: %s", exc)

    return response


@app.middleware("http")
async def csrf_middleware(request: Request, call_next):
    unsafe = request.method in {"POST", "PUT", "PATCH", "DELETE"}
    public_paths = (
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/logout",
        "/api/v1/auth/csrf-token",
        "/api/v1/auth/verify-csrf",
        "/api/v1/billing/webhook",
        "/api/v1/contact",
        # Chat is a stateless, rate-limited public endpoint with no cookie-driven
        # side effects, so it is reachable before a CSRF token exists.
        "/api/v1/chat",
        "/api/v1/connectors/test",
    )
    if unsafe and not request.url.path.startswith(public_paths):
        has_api_key = bool(request.headers.get("x-api-key"))
        has_bearer = (request.headers.get("authorization") or "").lower().startswith("bearer ")
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get("x-csrf-token")
        if not has_api_key and not has_bearer and not verify_csrf_token(header_token, cookie_token):
            # This middleware runs outside the router, so raising here would escape
            # the exception handlers and surface as a 500 instead of a 403.
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token missing or invalid"},
            )
    return await call_next(request)


@app.get("/")
async def root():
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running",
        "timestamp": utcnow().isoformat(),
    }


@app.get("/health")
async def health():
    try:
        async with async_session_factory() as db:
            await db.execute(select(1))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc
    return {
        "status": "healthy",
        "timestamp": utcnow().isoformat(),
    }


@app.get("/metrics", include_in_schema=False)
async def metrics() -> Response:
    """Prometheus exposition endpoint scraped by the `backend` job."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(billing.router, prefix="/api/v1/billing", tags=["Billing"])
app.include_router(api_keys.router, prefix="/api/v1/api-keys", tags=["API Keys"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(contact.router, prefix="/api/v1", tags=["Contact"])

app.include_router(tenants.router, prefix="/api/v1/tenants", tags=["Tenants"], dependencies=[Depends(require_platform_user)])
app.include_router(work_groups.router, prefix="/api/v1/work-groups", tags=["Work Groups"])
app.include_router(knowledge_bases.router, prefix="/api/v1/knowledge-bases", tags=["Knowledge Bases"], dependencies=[Depends(require_platform_user)])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"], dependencies=[Depends(require_platform_user)])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"], dependencies=[Depends(require_platform_user)])
app.include_router(rag.router, prefix="/api/v1/rag", tags=["RAG"], dependencies=[Depends(require_platform_user)])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Workflows"], dependencies=[Depends(require_platform_user)])
app.include_router(metadata.router, prefix="/api/v1/metadata", tags=["Metadata"], dependencies=[Depends(require_platform_user)])
app.include_router(evaluation.router, prefix="/api/v1/evaluation", tags=["Evaluation"], dependencies=[Depends(require_platform_user)])
app.include_router(governance.router, prefix="/api/v1/governance", tags=["Governance"], dependencies=[Depends(require_platform_user)])
app.include_router(connectors.router, prefix="/api/v1/connectors", tags=["Connectors"], dependencies=[Depends(require_platform_user)])
app.include_router(connectors.public_router, prefix="/api/v1/connectors", tags=["Connectors"])
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["Profiles"], dependencies=[Depends(require_platform_user)])
app.include_router(platform.router, prefix="/api/v1", tags=["Platform"], dependencies=[Depends(require_platform_user)])
app.include_router(system.router, prefix="/api/v1", tags=["System"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
