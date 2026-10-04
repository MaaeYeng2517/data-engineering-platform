"""Tests for the service profile feature.

The profile feature stores provider tokens, so the parts worth pinning down are
the ones that could leak a secret or let an operator point a probe at something
dangerous: the masking helpers, the response serializers that must never emit
ciphertext or plaintext, the request validation, and the health-check guards.
No database is needed — the serializers take model objects directly.
"""
import uuid
from datetime import datetime

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from backend.app.api import profiles as profiles_api
from backend.app.models.profile import (
    Profile,
    ProfileConfigItem,
    ProfileService,
    ServiceHealth,
)
from backend.app.schemas import (
    ProfileConfigItemCreate,
    ProfileCreate,
    ProfileServiceCreate,
    ProfileServiceUpdate,
)
from backend.app.services import profile_secrets
from backend.app.services.profiles import validate_health_check_url
from backend.app.utils.time import utcnow
from backend.main import app

SECRET = "sk-live-9f8a7b6c5d4e3f2a1b0c"


def _profile(**overrides) -> Profile:
    defaults = {
        "id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "owner_id": uuid.uuid4(),
        "name": "Production EU",
        "slug": "production-eu",
        "description": None,
        "environment": "production",
        "cloud_provider": "aws",
        "region": "eu-central-1",
        "zone": "eu-central-1a",
        "variables": {"LOG_LEVEL": "info"},
        "tags": ["critical"],
        "is_default": True,
        "is_active": True,
        "created_at": utcnow(),
        "updated_at": utcnow(),
        "services": [],
        "config_items": [],
    }
    return Profile(**{**defaults, **overrides})


def _service(**overrides) -> ProfileService:
    defaults = {
        "id": uuid.uuid4(),
        "profile_id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "name": "OpenAI",
        "service_type": "llm",
        "provider": "openai",
        "description": None,
        "api_base_url": "https://api.openai.com/v1",
        "host": None,
        "port": None,
        "region": None,
        "zone": None,
        "auth_type": "api_key",
        "token_encrypted": profile_secrets.encrypt_secret(SECRET),
        "username": None,
        "credentials_encrypted": None,
        "env_vars": {},
        "headers": {},
        "timeout_seconds": 30,
        "max_retries": 3,
        "health_check_url": None,
        "health_check_enabled": False,
        "health_status": ServiceHealth.UNKNOWN.value,
        "last_checked_at": None,
        "is_active": True,
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    return ProfileService(**{**defaults, **overrides})


def _config_item(**overrides) -> ProfileConfigItem:
    defaults = {
        "id": uuid.uuid4(),
        "profile_id": uuid.uuid4(),
        "tenant_id": uuid.uuid4(),
        "key": "DATABASE_URL",
        "value": "postgresql://localhost:5432/dataair",
        "description": None,
        "value_type": "string",
        "is_secret": False,
        "tags": [],
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    return ProfileConfigItem(**{**defaults, **overrides})


# --- secret helpers ---------------------------------------------------------


def test_ciphertext_does_not_contain_the_plaintext():
    encrypted = profile_secrets.encrypt_secret(SECRET)

    assert encrypted != SECRET
    assert SECRET not in encrypted
    assert profile_secrets.decrypt_secret(encrypted) == SECRET


def test_mask_keeps_the_ends_but_not_the_middle():
    masked = profile_secrets.mask_secret(SECRET)

    assert masked.startswith(SECRET[:4])
    assert masked.endswith(SECRET[-4:])
    assert "9f8a7b" not in masked


def test_short_secret_is_masked_entirely():
    # Masking must not become a leak when the value is shorter than the window.
    assert profile_secrets.mask_secret("short") == "*" * 5


def test_mask_and_encrypt_pass_through_none():
    assert profile_secrets.mask_secret(None) is None
    assert profile_secrets.encrypt_secret(None) is None
    assert profile_secrets.decrypt_secret(None) is None


def test_undecryptable_secret_returns_none_instead_of_raising(monkeypatch):
    encrypted = profile_secrets.encrypt_secret(SECRET)
    monkeypatch.setattr(profile_secrets, "PROFILE_SECRET_KEY", "a-rotated-key")

    # One unreadable row must not break a whole listing, so this is None and not
    # an InvalidToken exception.
    assert profile_secrets.decrypt_secret(encrypted) is None


def test_json_blob_round_trip():
    payload = {"client_id": "abc", "client_secret": "shh"}

    encrypted = profile_secrets.encrypt_json(payload)

    assert profile_secrets.decrypt_json(encrypted) == payload


def test_empty_json_blob_decodes_to_empty_dict():
    assert profile_secrets.decrypt_json(None) == {}
    assert profile_secrets.encrypt_json({}) is None


# --- response serialisation -------------------------------------------------


def test_service_response_never_leaks_the_token():
    response = profiles_api._service_response(_service())

    assert response.has_token is True
    assert response.token_masked.startswith(SECRET[:4])
    # Neither the plaintext nor the stored ciphertext may appear anywhere.
    dumped = response.model_dump_json()
    assert SECRET not in dumped
    assert _service().token_encrypted not in dumped


def test_service_response_without_a_token_reports_none():
    response = profiles_api._service_response(_service(token_encrypted=None))

    assert response.has_token is False
    assert response.token_masked is None


def test_secret_config_item_value_is_withheld():
    item = _config_item(is_secret=True, value=profile_secrets.encrypt_secret(SECRET))

    response = profiles_api._config_response(item)

    assert response.value is None
    assert response.value_masked is not None
    assert SECRET not in response.model_dump_json()


def test_plain_config_item_value_is_returned():
    response = profiles_api._config_response(_config_item())

    assert response.value == "postgresql://localhost:5432/dataair"
    assert response.value_masked is None


def test_profile_response_counts_children():
    profile = _profile(services=[_service()], config_items=[_config_item(), _config_item(key="X")])

    response = profiles_api._profile_response(profile)

    assert response.service_count == 1
    assert response.config_count == 2


def test_detail_response_includes_services_and_config():
    profile = _profile(services=[_service()], config_items=[_config_item()])

    detail = profiles_api._detail_response(profile)

    assert len(detail.services) == 1
    assert len(detail.config_items) == 1
    assert SECRET not in detail.model_dump_json()


async def test_resolved_view_omits_secrets(monkeypatch):
    profile = _profile(
        services=[_service()],
        config_items=[_config_item(is_secret=True, value=profile_secrets.encrypt_secret(SECRET))],
    )

    async def fake_get_profile(*args, **kwargs):
        return profile

    monkeypatch.setattr(profiles_api, "_get_profile", fake_get_profile)

    resolved = await profiles_api.resolve_profile(profile.id, user=_caller(), db=None)

    assert resolved.services[0].token is None
    assert resolved.config["DATABASE_URL"] is None
    assert resolved.variables == {"LOG_LEVEL": "info"}
    assert SECRET not in resolved.model_dump_json()


def _caller():
    return type("U", (), {"tenant_id": uuid.uuid4(), "email": "ops@example.com"})()


# --- request validation -----------------------------------------------------


def test_service_requires_an_endpoint():
    with pytest.raises(ValidationError, match="api_base_url or host"):
        ProfileServiceCreate(name="OpenAI")


def test_service_accepts_a_host_without_a_url():
    service = ProfileServiceCreate(name="MinIO", host="minio", port=9000)

    assert service.port == 9000


def test_service_name_is_stripped():
    assert ProfileServiceCreate(name="  OpenAI  ", api_base_url="https://x").name == "OpenAI"


def test_service_rejects_a_blank_name():
    with pytest.raises(ValidationError):
        ProfileServiceCreate(name="   ", api_base_url="https://x")


def test_port_bounds_are_enforced():
    with pytest.raises(ValidationError):
        ProfileServiceCreate(name="x", api_base_url="https://x", port=70000)


def test_profile_name_is_stripped_and_tags_cleaned():
    profile = ProfileCreate(name="  Production EU  ", tags=[" critical ", "", "  "])

    assert profile.name == "Production EU"
    assert profile.tags == ["critical"]


def test_config_item_rejects_an_unknown_value_type():
    with pytest.raises(ValidationError):
        ProfileConfigItemCreate(key="X", value="1", value_type="blob")


def test_config_item_normalises_value_type():
    assert ProfileConfigItemCreate(key="X", value_type="JSON").value_type == "json"


def test_config_item_key_is_stripped():
    assert ProfileConfigItemCreate(key="  RETRIES  ").key == "RETRIES"


def test_service_update_can_rotate_a_token():
    assert ProfileServiceUpdate(token="new-secret").token == "new-secret"
    assert ProfileServiceUpdate().token is None


# --- health check guards ----------------------------------------------------


def test_health_check_uses_the_explicit_url():
    assert validate_health_check_url("https://api.example.com", "https://probe.example.com/ping") == (
        "https://probe.example.com/ping"
    )


def test_health_check_resolves_a_relative_path_against_the_base_url():
    assert validate_health_check_url("https://api.example.com/v1", "/health") == (
        "https://api.example.com/health"
    )


def test_health_check_falls_back_to_the_api_base_url():
    assert validate_health_check_url("https://api.example.com", None) == "https://api.example.com"


def test_health_check_requires_some_endpoint():
    with pytest.raises(HTTPException) as excinfo:
        validate_health_check_url(None, None)

    assert excinfo.value.status_code == 400


def test_health_check_rejects_a_non_http_scheme():
    with pytest.raises(HTTPException) as excinfo:
        validate_health_check_url(None, "file:///etc/passwd")

    assert excinfo.value.status_code == 400
    assert "http" in excinfo.value.detail


@pytest.mark.parametrize(
    "host",
    ["http://169.254.169.254/latest/meta-data/", "http://metadata.google.internal/"],
)
def test_health_check_refuses_instance_metadata_endpoints(host):
    with pytest.raises(HTTPException) as excinfo:
        validate_health_check_url(None, host)

    assert excinfo.value.status_code == 400
    assert "metadata" in excinfo.value.detail


# --- slugs and routing ------------------------------------------------------


def test_slugify_handles_accented_and_symbol_names():
    assert profiles_api._slugify("Production (EU-West)") == "production-eu-west"


def test_slugify_never_returns_an_empty_slug():
    assert profiles_api._slugify("***") == "profile"


def test_profile_routes_are_registered():
    paths = {route.path for route in app.routes}

    assert "/api/v1/profiles" in paths
    assert "/api/v1/profiles/{profile_id}/services" in paths
    assert "/api/v1/profiles/{profile_id}/config/{item_id}" in paths


def _guard_calls(path: str, method: str = "GET"):
    """The dependency functions guarding one route."""
    route = next(
        r
        for r in app.routes
        if getattr(r, "path", "") == path and method in (getattr(r, "methods", None) or set())
    )
    return [dep.call for dep in route.dependant.dependencies]


def test_secret_routes_are_not_public():
    """The profile tree hangs off the authenticated router, and the two
    secret-bearing endpoints additionally require an admin."""
    from backend.app.dependencies import require_admin, require_platform_user

    secret_path = "/api/v1/profiles/{profile_id}/services/{service_id}/secret"
    health_path = "/api/v1/profiles/{profile_id}/services/{service_id}/health-check"

    assert require_admin in _guard_calls(secret_path)
    assert require_platform_user in _guard_calls(secret_path)
    assert require_admin in _guard_calls(health_path, method="POST")


async def test_options_endpoint_lists_every_enum():
    from backend.app.models.profile import AuthType, CloudProvider, ProfileEnvironment, ServiceType

    payload = await profiles_api.profile_options(user=_caller())

    assert payload["environments"] == [item.value for item in ProfileEnvironment]
    assert payload["cloud_providers"] == [item.value for item in CloudProvider]
    assert payload["service_types"] == [item.value for item in ServiceType]
    assert payload["health_statuses"] == [item.value for item in ServiceHealth]
    assert "api_key" in [item.value for item in AuthType]


def test_profiles_require_authentication():
    from backend.app.dependencies import require_platform_user

    assert require_platform_user in _guard_calls("/api/v1/profiles")


def test_datetime_fields_are_iso_formatted():
    response = profiles_api._service_response(_service())

    assert isinstance(response.created_at, datetime)
    assert "T" in response.model_dump_json()
