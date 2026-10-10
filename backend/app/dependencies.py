"""Shared FastAPI dependencies for authentication and authorization."""
import logging

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.api_key import ApiKey
from backend.app.models.user import User, UserRole
from backend.app.security import ACCESS_TOKEN_COOKIE_NAME, decode_token, hash_api_key
from backend.app.utils.time import utcnow
from backend.config import ADMIN_EMAILS
from backend.database import get_db

logger = logging.getLogger(__name__)

_UNAUTHENTICATED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)


def _bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization") or ""
    if header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return None


def _request_token(request: Request) -> str | None:
    return _bearer_token(request) or request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)


async def _load_active_user(db: AsyncSession, user_id) -> User:
    """Load a user and reject the account or its workspace if either is disabled."""
    result = await db.execute(
        select(User).options(selectinload(User.tenant)).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise _UNAUTHENTICATED
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    if user.tenant is not None and not user.tenant.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Workspace is disabled")
    return user


async def resolve_api_key(db: AsyncSession, raw_key: str) -> ApiKey:
    """Resolve an ``x-api-key`` value to its key record.

    The stored digest is an HMAC of the raw key, so lookup is a single indexed
    equality and the plaintext never has to be compared in the database.
    """
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == hash_api_key(raw_key))
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise _UNAUTHENTICATED
    if not api_key.is_active or api_key.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key is revoked")
    if api_key.expires_at is not None and api_key.expires_at <= utcnow():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key has expired")
    return api_key


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Resolve the authenticated user.

    Three credentials are accepted: an API key, a bearer token, and the access
    cookie the browser client uses. An API key identifies the user directly;
    a token names one and is then re-read from the database.
    """
    raw_key = request.headers.get("x-api-key")
    if raw_key:
        api_key = await resolve_api_key(db, raw_key.strip())
        # Recorded here rather than in middleware: this is the only place that
        # knows which key a request arrived with.
        request.state.api_key_id = str(api_key.id)
        user = await _load_active_user(db, api_key.user_id)
        request.state.user_id = str(user.id)
        request.state.tenant_id = str(user.tenant_id)
        api_key.last_used_at = utcnow()
        return user

    token = _request_token(request)
    if not token:
        raise _UNAUTHENTICATED

    try:
        payload = decode_token(token, "access")
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("Token has no user_id claim")
    except Exception as exc:
        raise _UNAUTHENTICATED from exc

    user = await _load_active_user(db, user_id)
    request.state.user_id = str(user.id)
    request.state.tenant_id = str(user.tenant_id)
    return user


async def require_platform_user(user: User = Depends(get_current_user)) -> User:
    """Router-level guard requiring an authenticated, active account."""
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is disabled")
    return user


async def get_optional_user(request: Request, db: AsyncSession = Depends(get_db)) -> User | None:
    """Resolve the user when a valid token is present, otherwise return None."""
    if not _request_token(request):
        return None
    try:
        return await get_current_user(request, db)
    except HTTPException:
        return None


async def require_admin(user: User = Depends(get_current_user)) -> User:
    """Guard for administrative endpoints."""
    if user.role != UserRole.ADMIN and not user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin privileges required")
    return user


async def sync_admin_role(user: User) -> User:
    """Promote or demote a user so their role matches ADMIN_EMAILS."""
    email = (user.email or "").strip().lower()
    should_be_admin = bool(email) and email in ADMIN_EMAILS

    if should_be_admin and user.role != UserRole.ADMIN:
        user.role = UserRole.ADMIN
        user.is_superuser = True
    elif not should_be_admin and user.role == UserRole.ADMIN and not user.is_superuser:
        user.role = UserRole.MEMBER
    return user
