"""Encryption helpers for service profile secrets.

Provider tokens and credentials are stored encrypted at rest and are never
returned by list or detail responses. Callers get a masked preview instead, and
a single admin-only endpoint can reveal the plaintext on purpose.
"""
import base64
import hashlib
import json
import logging
from typing import Any, Optional

from cryptography.fernet import Fernet, InvalidToken

from backend.config import PROFILE_SECRET_KEY

logger = logging.getLogger(__name__)

# How many leading/trailing characters a mask keeps visible.
_MASK_VISIBLE = 4
# Below this length a mask would reveal the whole value, so show nothing but a
# placeholder that still communicates the value is set.
_MASK_MIN_LENGTH = 12

_FERNET_KEY_PREFIX = b"dataair-profile-secrets:v1:"


def _fernet() -> Fernet:
    """Derive the Fernet key from the configured secret."""
    digest = hashlib.sha256(_FERNET_KEY_PREFIX + PROFILE_SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def encrypt_secret(value: Optional[str]) -> Optional[str]:
    """Encrypt a secret for storage, or return None for an absent value."""
    if value is None:
        return None
    return _fernet().encrypt(value.encode()).decode()


def decrypt_secret(payload: Optional[str]) -> Optional[str]:
    """Decrypt a stored secret, returning None when it cannot be read."""
    if not payload:
        return None
    try:
        return _fernet().decrypt(payload.encode()).decode()
    except (InvalidToken, ValueError):
        # Almost always a rotated PROFILE_SECRET_KEY. Surfacing None beats
        # raising, so one unreadable row cannot break a whole listing.
        logger.warning("Stored profile secret could not be decrypted; key likely rotated")
        return None


def mask_secret(value: Optional[str]) -> Optional[str]:
    """Return a display-safe preview that keeps the ends of a secret visible."""
    if value is None:
        return None
    if not value:
        return ""
    if len(value) < _MASK_MIN_LENGTH:
        return "*" * len(value)
    return f"{value[:_MASK_VISIBLE]}{'*' * 8}{value[-_MASK_VISIBLE:]}"


def encrypt_json(payload: Optional[dict[str, Any]]) -> Optional[str]:
    """Encrypt a JSON object (extra credentials) for storage."""
    if not payload:
        return None
    return encrypt_secret(json.dumps(payload))


def decrypt_json(payload: Optional[str]) -> dict[str, Any]:
    """Decrypt a stored JSON object, returning an empty dict when unreadable."""
    plaintext = decrypt_secret(payload)
    if not plaintext:
        return {}
    try:
        decoded = json.loads(plaintext)
    except ValueError:
        logger.warning("Stored profile credential blob was not valid JSON")
        return {}
    return decoded if isinstance(decoded, dict) else {}
