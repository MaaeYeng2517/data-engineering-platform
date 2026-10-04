"""Security primitives: password hashing, JWT and CSRF tokens."""
import hashlib
import hmac
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Response
from passlib.context import CryptContext
from starlette.responses import Response as StarletteResponse

from backend.config import (
    API_KEY_HMAC_SECRET,
    COOKIE_SAMESITE,
    COOKIE_SECURE,
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
    JWT_ALGORITHM,
    JWT_REFRESH_TOKEN_EXPIRE_DAYS,
    JWT_SECRET_KEY,
)

logger = logging.getLogger(__name__)

ACCESS_TOKEN_COOKIE_NAME = "dataair_access_token"
REFRESH_TOKEN_COOKIE_NAME = "dataair_refresh_token"
CSRF_COOKIE_NAME = "dataair_csrf_token"

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

API_KEY_PREFIX = "dk"
API_KEY_PREFIX_LENGTH = 12

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return _pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a stored hash."""
    try:
        return _pwd_context.verify(password, hashed_password)
    except ValueError:
        logger.warning("Password verification failed against an unreadable hash")
        return False


def _encode(payload: dict[str, Any], expires: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    body = {
        **payload,
        "type": token_type,
        "iat": int(now.timestamp()),
        "exp": int((now + expires).timestamp()),
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(body, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(payload: dict[str, Any]) -> str:
    """Issue a short-lived access token."""
    return _encode(payload, timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES), ACCESS_TOKEN_TYPE)


def create_refresh_token(payload: dict[str, Any]) -> str:
    """Issue a long-lived refresh token."""
    return _encode(payload, timedelta(days=JWT_REFRESH_TOKEN_EXPIRE_DAYS), REFRESH_TOKEN_TYPE)


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Decode a token and assert it carries the expected type."""
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    if payload.get("type") != expected_type:
        raise ValueError(f"Expected a {expected_type} token")
    return payload


def create_csrf_token() -> str:
    """Create a CSRF token bound to a random nonce."""
    return secrets.token_urlsafe(32)


def verify_csrf_token(header_token: str | None, cookie_token: str | None) -> bool:
    """Compare the CSRF header against the CSRF cookie in constant time."""
    if not header_token or not cookie_token:
        return False
    return hmac.compare_digest(header_token, cookie_token)


def hash_api_key(raw_key: str) -> str:
    """Derive the stored digest for an API key."""
    return hmac.new(
        API_KEY_HMAC_SECRET.encode(),
        raw_key.encode(),
        hashlib.sha256,
    ).hexdigest()


def generate_api_key() -> tuple[str, str, str]:
    """Create a new API key, returning (plain_key, key_prefix, key_hash)."""
    secret = secrets.token_urlsafe(32)
    raw_key = f"{API_KEY_PREFIX}_{secret}"
    return raw_key, raw_key[:API_KEY_PREFIX_LENGTH], hash_api_key(raw_key)


def _set_cookie(response: StarletteResponse, name: str, value: str, max_age: int) -> None:
    response.set_cookie(
        name,
        value,
        max_age=max_age,
        httponly=name != CSRF_COOKIE_NAME,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )


def set_auth_cookies(
    response: Response,
    access_token: str,
    refresh_token: str,
    csrf_token: str,
) -> None:
    """Persist the token triple as cookies."""
    _set_cookie(response, ACCESS_TOKEN_COOKIE_NAME, access_token, JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    _set_cookie(response, REFRESH_TOKEN_COOKIE_NAME, refresh_token, JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400)
    _set_cookie(response, CSRF_COOKIE_NAME, csrf_token, 60 * 60)


def clear_auth_cookies(response: Response) -> None:
    """Remove every auth cookie."""
    for name in (ACCESS_TOKEN_COOKIE_NAME, REFRESH_TOKEN_COOKIE_NAME, CSRF_COOKIE_NAME):
        response.delete_cookie(name, path="/")
