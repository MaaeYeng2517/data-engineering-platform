"""Shared FastAPI dependencies for authentication and authorization."""
import logging

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.user import User, UserRole
from backend.app.security import ACCESS_TOKEN_COOKIE_NAME, decode_token
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


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> User:
    """Resolve the authenticated user from a bearer token or the access cookie."""
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
