"""Helpers for probing the services registered on a profile.

A profile holds user-authored URLs, so a health check is an outbound request to
whatever the operator typed. The guards here keep that request on http(s) and
away from cloud instance-metadata endpoints, which hand out node credentials to
anyone who can reach them.
"""
import logging
from typing import Optional
from urllib.parse import urljoin, urlsplit

import httpx
from fastapi import HTTPException

from backend.app.models.profile import ProfileService, ServiceHealth
from backend.app.utils.time import utcnow
from backend.config import (
    PROFILE_HEALTH_CHECK_MAX_TIMEOUT_SECONDS,
    PROFILE_HEALTH_CHECK_TIMEOUT_SECONDS,
)

logger = logging.getLogger(__name__)

_ALLOWED_SCHEMES = {"http", "https"}

# Hostnames that return node credentials rather than a health payload.
_BLOCKED_HOSTS = {
    "169.254.169.254",
    "metadata.google.internal",
    "metadata.goog",
    "instance-data",
    "metadata",
}


def _assert_safe(url: str) -> None:
    """Reject a probe target that is not a plain http(s) service endpoint."""
    parts = urlsplit(url)
    if parts.scheme.lower() not in _ALLOWED_SCHEMES:
        raise HTTPException(
            status_code=400,
            detail=f"Health check URL must use http or https, got '{parts.scheme or 'no scheme'}'",
        )
    host = (parts.hostname or "").strip().lower()
    if not host:
        raise HTTPException(status_code=400, detail="Health check URL has no host")
    if host in _BLOCKED_HOSTS:
        raise HTTPException(
            status_code=400,
            detail="Refusing to probe an instance-metadata endpoint",
        )


def validate_health_check_url(
    base_url: Optional[str],
    check_url: Optional[str],
) -> str:
    """Resolve the URL to probe for a service, or raise 400.

    An explicit `health_check_url` wins. Otherwise the service's own API base URL
    is probed, which is the case when an operator registers an internal service
    such as the bundled MinIO or Qdrant instance.
    """
    if check_url:
        candidate = check_url.strip()
        if not candidate.startswith(("http://", "https://")):
            candidate = urljoin(base_url or "http://localhost/", candidate)
        _assert_safe(candidate)
        return candidate

    if not base_url:
        raise HTTPException(
            status_code=400,
            detail="Set health_check_url or api_base_url before running a health check",
        )
    _assert_safe(base_url)
    return base_url


async def check_service_health(service: ProfileService, target: str) -> ServiceHealth:
    """Probe one endpoint and record the result on the service row."""
    timeout = min(
        float(service.timeout_seconds or PROFILE_HEALTH_CHECK_TIMEOUT_SECONDS),
        PROFILE_HEALTH_CHECK_MAX_TIMEOUT_SECONDS,
    )
    headers = {
        key: value
        for key, value in (service.headers or {}).items()
        if isinstance(key, str) and isinstance(value, str)
    }

    status_code: Optional[int] = None
    detail = ""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(target, headers=headers)
            status_code = response.status_code
    except httpx.HTTPError as exc:
        # An unreachable endpoint is the answer, not an exception for the caller.
        detail = exc.__class__.__name__
        logger.info("Health check for %s failed: %s", service.name, detail)

    if status_code is None:
        service.health_status = ServiceHealth.DOWN.value
    elif status_code < 400:
        service.health_status = ServiceHealth.HEALTHY.value
    elif status_code < 500:
        # 4xx means the endpoint answered but rejected the probe.
        service.health_status = ServiceHealth.DEGRADED.value
    else:
        service.health_status = ServiceHealth.DOWN.value

    service.last_checked_at = utcnow()
    if detail:
        logger.debug("Health check detail for %s: %s", service.name, detail)
    return ServiceHealth(service.health_status)
