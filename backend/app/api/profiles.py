"""Service profile endpoints.

Profiles group the configuration and the reachable services of one environment
(development, staging, production, …) so an operator can add, edit and remove a
hosting target, its cloud region and each service's endpoint and token from one
place instead of scattering them across `.env` files.
"""
import logging
import re
import unicodedata
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.dependencies import require_admin, require_platform_user
from backend.app.models.profile import (
    CloudProvider,
    Profile,
    ProfileConfigItem,
    ProfileEnvironment,
    ProfileService,
    ServiceHealth,
    ServiceType,
)
from backend.app.models.user import User
from backend.app.schemas import (
    ProfileConfigItemCreate,
    ProfileConfigItemResponse,
    ProfileConfigItemUpdate,
    ProfileCreate,
    ProfileDetailResponse,
    ProfileResolvedResponse,
    ProfileResolvedService,
    ProfileResponse,
    ProfileServiceCreate,
    ProfileServiceResponse,
    ProfileServiceSecretResponse,
    ProfileServiceUpdate,
    ProfileUpdate,
)
from backend.app.services.profile_secrets import (
    decrypt_json,
    decrypt_secret,
    encrypt_json,
    encrypt_secret,
    mask_secret,
)
from backend.app.services.profiles import (
    check_service_health,
    validate_health_check_url,
)
from backend.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")

# Hostnames that hand out credentials to anything on the network. A profile is
# user-authored, so a health check must never be aimed at one of these.
_BLOCKED_HEALTH_HOSTS = {
    "169.254.169.254",
    "metadata.google.internal",
    "metadata.goog",
    "instance-data",
}


def _slugify(value: str) -> str:
    """Turn a display name into a URL-safe slug."""
    normalized = unicodedata.normalize("NFKD", value)
    ascii_only = normalized.encode("ascii", "ignore").decode().lower()
    slug = _SLUG_STRIP.sub("-", ascii_only).strip("-")
    return slug or "profile"


async def _unique_slug(db: AsyncSession, tenant_id: UUID, name: str, exclude_id: Optional[UUID] = None) -> str:
    """Derive a slug for a profile that does not collide inside the tenant."""
    base = _slugify(name)
    candidate = base
    suffix = 2
    while True:
        query = select(Profile.id).where(
            Profile.tenant_id == tenant_id,
            Profile.slug == candidate,
        )
        if exclude_id is not None:
            query = query.where(Profile.id != exclude_id)
        if (await db.execute(query)).scalar_one_or_none() is None:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


async def _clear_default_flags(db: AsyncSession, tenant_id: UUID, keep_id: Optional[UUID] = None) -> None:
    """Ensure at most one profile per tenant is the default."""
    query = select(Profile).where(Profile.tenant_id == tenant_id, Profile.is_default.is_(True))
    if keep_id is not None:
        query = query.where(Profile.id != keep_id)
    for other in (await db.execute(query)).scalars().all():
        other.is_default = False


async def _get_profile(db: AsyncSession, tenant_id: UUID, profile_id: UUID) -> Profile:
    """Load a profile inside the caller's tenant or raise 404."""
    result = await db.execute(
        select(Profile)
        .options(selectinload(Profile.services), selectinload(Profile.config_items))
        .where(Profile.id == profile_id, Profile.tenant_id == tenant_id)
    )
    profile = result.scalar_one_or_none()
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


def _service_response(service: ProfileService) -> ProfileServiceResponse:
    """Serialise a service, replacing ciphertext with a masked preview."""
    response = ProfileServiceResponse.model_validate(service)
    token = decrypt_secret(service.token_encrypted)
    response.has_token = bool(service.token_encrypted)
    response.has_credentials = bool(service.credentials_encrypted)
    response.token_masked = mask_secret(token) if token else None
    return response


def _config_response(item: ProfileConfigItem) -> ProfileConfigItemResponse:
    """Serialise a config item, withholding the plaintext of a secret."""
    response = ProfileConfigItemResponse.model_validate(item)
    if item.is_secret:
        value = decrypt_secret(item.value)
        response.value = None
        response.value_masked = mask_secret(value) if value else None
    return response


def _profile_response(profile: Profile) -> ProfileResponse:
    response = ProfileResponse.model_validate(profile)
    response.service_count = len(profile.services or [])
    response.config_count = len(profile.config_items or [])
    return response


def _detail_response(profile: Profile) -> ProfileDetailResponse:
    detail = ProfileDetailResponse(**_profile_response(profile).model_dump())
    detail.services = [_service_response(service) for service in profile.services or []]
    detail.config_items = [_config_response(item) for item in profile.config_items or []]
    return detail


async def _get_service(db: AsyncSession, profile: Profile, service_id: UUID) -> ProfileService:
    for service in profile.services or []:
        if service.id == service_id:
            return service
    raise HTTPException(status_code=404, detail="Service not found in profile")


async def _get_config_item(db: AsyncSession, profile: Profile, item_id: UUID) -> ProfileConfigItem:
    for item in profile.config_items or []:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Configuration item not found in profile")


@router.get("", response_model=List[ProfileResponse])
@router.get("/", response_model=List[ProfileResponse], include_in_schema=False)
async def list_profiles(
    environment: Optional[ProfileEnvironment] = None,
    cloud_provider: Optional[CloudProvider] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = Query(None, max_length=120),
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Profile).options(selectinload(Profile.services), selectinload(Profile.config_items))
    query = query.where(Profile.tenant_id == user.tenant_id)
    if environment is not None:
        query = query.where(Profile.environment == environment.value)
    if cloud_provider is not None:
        query = query.where(Profile.cloud_provider == cloud_provider.value)
    if is_active is not None:
        query = query.where(Profile.is_active.is_(is_active))
    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(or_(Profile.name.ilike(term), Profile.slug.ilike(term)))

    result = await db.execute(query.order_by(Profile.is_default.desc(), Profile.name))
    return [_profile_response(profile) for profile in result.scalars().all()]


@router.post("", response_model=ProfileDetailResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ProfileDetailResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_profile(
    payload: ProfileCreate,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a profile. The first profile in a tenant becomes the default."""
    slug = payload.slug.strip() if payload.slug else await _unique_slug(db, user.tenant_id, payload.name)
    existing = await db.execute(
        select(Profile.id).where(Profile.tenant_id == user.tenant_id, Profile.slug == slug)
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail=f"Profile slug '{slug}' already exists")

    is_default = payload.is_default
    if not is_default:
        count = await db.execute(
            select(func.count(Profile.id)).where(Profile.tenant_id == user.tenant_id)
        )
        is_default = (count.scalar() or 0) == 0

    profile = Profile(
        tenant_id=user.tenant_id,
        owner_id=user.id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        environment=payload.environment.value,
        cloud_provider=payload.cloud_provider.value,
        region=payload.region,
        zone=payload.zone,
        variables=payload.variables,
        tags=payload.tags,
        is_default=is_default,
        is_active=payload.is_active,
    )
    db.add(profile)
    await db.commit()
    logger.info("Created profile %s (%s) for tenant %s", profile.id, profile.slug, user.tenant_id)
    return _detail_response(await _get_profile(db, user.tenant_id, profile.id))


@router.get("/options", response_model=dict)
async def profile_options(user: User = Depends(require_platform_user)):
    """The enum values the UI needs to build its pickers."""
    return {
        "environments": [item.value for item in ProfileEnvironment],
        "cloud_providers": [item.value for item in CloudProvider],
        "service_types": [item.value for item in ServiceType],
        "health_statuses": [item.value for item in ServiceHealth],
    }


@router.get("/{profile_id}", response_model=ProfileDetailResponse)
async def get_profile(
    profile_id: UUID,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    return _detail_response(await _get_profile(db, user.tenant_id, profile_id))


@router.patch("/{profile_id}", response_model=ProfileDetailResponse)
@router.put("/{profile_id}", response_model=ProfileDetailResponse, include_in_schema=False)
async def update_profile(
    profile_id: UUID,
    payload: ProfileUpdate,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(db, user.tenant_id, profile_id)
    data = payload.model_dump(exclude_unset=True)

    if data.get("is_default"):
        await _clear_default_flags(db, user.tenant_id, keep_id=profile.id)
    if "slug" in data and data["slug"]:
        candidate = _slugify(data["slug"])
        clash = await db.execute(
            select(Profile.id).where(
                Profile.tenant_id == user.tenant_id,
                Profile.slug == candidate,
                Profile.id != profile.id,
            )
        )
        if clash.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail=f"Profile slug '{candidate}' already exists")
        data["slug"] = candidate
    elif "name" in data and not profile.slug:
        data["slug"] = await _unique_slug(db, user.tenant_id, data["name"], exclude_id=profile.id)

    for field, value in data.items():
        if field in {"environment", "cloud_provider"} and value is not None:
            value = value.value
        setattr(profile, field, value)

    await db.commit()
    return _detail_response(await _get_profile(db, user.tenant_id, profile_id))


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: UUID,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(db, user.tenant_id, profile_id)
    await db.delete(profile)
    await db.commit()


@router.post("/{profile_id}/duplicate", response_model=ProfileDetailResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_profile(
    profile_id: UUID,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    """Copy a profile with its services and config, leaving the slug unique."""
    source = await _get_profile(db, user.tenant_id, profile_id)
    name = f"{source.name} copy"
    copy = Profile(
        tenant_id=user.tenant_id,
        owner_id=user.id,
        name=name,
        slug=await _unique_slug(db, user.tenant_id, name),
        description=source.description,
        environment=source.environment,
        cloud_provider=source.cloud_provider,
        region=source.region,
        zone=source.zone,
        # Variables and tags are copied by value, not shared.
        variables=dict(source.variables or {}),
        tags=list(source.tags or []),
        is_default=False,
        is_active=source.is_active,
    )
    db.add(copy)
    await db.flush()

    for service in source.services or []:
        db.add(
            ProfileService(
                profile_id=copy.id,
                tenant_id=user.tenant_id,
                name=service.name,
                service_type=service.service_type,
                provider=service.provider,
                description=service.description,
                api_base_url=service.api_base_url,
                host=service.host,
                port=service.port,
                region=service.region,
                zone=service.zone,
                auth_type=service.auth_type,
                # Ciphertext is copied verbatim: the copy has the same secrets.
                token_encrypted=service.token_encrypted,
                username=service.username,
                credentials_encrypted=service.credentials_encrypted,
                env_vars=dict(service.env_vars or {}),
                headers=dict(service.headers or {}),
                timeout_seconds=service.timeout_seconds,
                max_retries=service.max_retries,
                health_check_url=service.health_check_url,
                health_check_enabled=service.health_check_enabled,
                is_active=service.is_active,
            )
        )
    for item in source.config_items or []:
        db.add(
            ProfileConfigItem(
                profile_id=copy.id,
                tenant_id=user.tenant_id,
                key=item.key,
                value=item.value,
                description=item.description,
                value_type=item.value_type,
                is_secret=item.is_secret,
                tags=list(item.tags or []),
            )
        )

    await db.commit()
    logger.info("Duplicated profile %s into %s", source.id, copy.id)
    return _detail_response(await _get_profile(db, user.tenant_id, copy.id))


@router.get("/{profile_id}/resolved", response_model=ProfileResolvedResponse)
async def resolve_profile(
    profile_id: UUID,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    """Flatten a profile into the config plus endpoints a consumer needs."""
    profile = await _get_profile(db, user.tenant_id, profile_id)
    return ProfileResolvedResponse(
        profile=_profile_response(profile),
        variables=dict(profile.variables or {}),
        config={
            item.key: (None if item.is_secret else item.value)
            for item in profile.config_items or []
        },
        services=[
            ProfileResolvedService(
                id=service.id,
                name=service.name,
                service_type=service.service_type,
                provider=service.provider,
                api_base_url=service.api_base_url,
                host=service.host,
                port=service.port,
                region=service.region,
                zone=service.zone,
                auth_type=service.auth_type,
                # Secret material is deliberately left out of the resolved view.
                username=service.username,
                env_vars=dict(service.env_vars or {}),
                headers=dict(service.headers or {}),
                timeout_seconds=service.timeout_seconds,
                max_retries=service.max_retries,
                health_status=service.health_status,
                is_active=service.is_active,
            )
            for service in profile.services or []
        ],
    )


@router.get("/{profile_id}/services", response_model=List[ProfileServiceResponse])
async def list_services(
    profile_id: UUID,
    service_type: Optional[ServiceType] = None,
    is_active: Optional[bool] = None,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(db, user.tenant_id, profile_id)
    services = profile.services or []
    if service_type is not None:
        services = [s for s in services if s.service_type == service_type.value]
    if is_active is not None:
        services = [s for s in services if s.is_active is is_active]
    return [_service_response(service) for service in services]


@router.post(
    "/{profile_id}/services",
    response_model=ProfileServiceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_service(
    profile_id: UUID,
    payload: ProfileServiceCreate,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(db, user.tenant_id, profile_id)
    if payload.health_check_enabled:
        validate_health_check_url(payload.api_base_url, payload.health_check_url)

    service = ProfileService(
        profile_id=profile.id,
        tenant_id=user.tenant_id,
        name=payload.name,
        service_type=payload.service_type.value,
        provider=payload.provider,
        description=payload.description,
        api_base_url=payload.api_base_url,
        host=payload.host,
        port=payload.port,
        region=payload.region,
        zone=payload.zone,
        auth_type=payload.auth_type.value,
        token_encrypted=encrypt_secret(payload.token),
        username=payload.username,
        credentials_encrypted=encrypt_json(payload.credentials),
        env_vars=payload.env_vars,
        headers=payload.headers,
        timeout_seconds=payload.timeout_seconds,
        max_retries=payload.max_retries,
        health_check_url=payload.health_check_url,
        health_check_enabled=payload.health_check_enabled,
        is_active=payload.is_active,
    )
    db.add(service)
    await db.commit()
    await db.refresh(service)
    logger.info("Added service %s to profile %s", service.name, profile.slug)
    return _service_response(service)


@router.get("/{profile_id}/services/{service_id}", response_model=ProfileServiceResponse)
async def get_service(
    profile_id: UUID,
    service_id: UUID,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(db, user.tenant_id, profile_id)
    return _service_response(await _get_service(db, profile, service_id))


@router.patch("/{profile_id}/services/{service_id}", response_model=ProfileServiceResponse)
@router.put("/{profile_id}/services/{service_id}", response_model=ProfileServiceResponse, include_in_schema=False)
async def update_service(
    profile_id: UUID,
    service_id: UUID,
    payload: ProfileServiceUpdate,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(db, user.tenant_id, profile_id)
    service = await _get_service(db, profile, service_id)
    data = payload.model_dump(exclude_unset=True)

    check_url = data.get("health_check_url", service.health_check_url)
    base_url = data.get("api_base_url", service.api_base_url)
    if data.get("health_check_enabled"):
        validate_health_check_url(base_url, check_url)

    # Secrets need the helpers rather than a plain assignment, so they are
    # applied separately from the declarative columns.
    token = data.pop("token", None)
    clear_token = data.pop("clear_token", False)
    credentials = data.pop("credentials", None)

    for field, value in data.items():
        if field == "service_type" and value is not None:
            value = value.value
        elif field == "auth_type" and value is not None:
            value = value.value
        setattr(service, field, value)

    if clear_token:
        service.token_encrypted = None
    elif token is not None:
        service.token_encrypted = encrypt_secret(token)
    if credentials is not None:
        service.credentials_encrypted = encrypt_json(credentials)

    await db.commit()
    return _service_response(await _get_service(db, profile, service_id))


@router.delete("/{profile_id}/services/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_service(
    profile_id: UUID,
    service_id: UUID,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(db, user.tenant_id, profile_id)
    service = await _get_service(db, profile, service_id)
    await db.delete(service)
    await db.commit()


@router.get(
    "/{profile_id}/services/{service_id}/secret",
    response_model=ProfileServiceSecretResponse,
)
async def reveal_service_secret(
    profile_id: UUID,
    service_id: UUID,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Return the plaintext token. Admin-only, because this is the one path
    that hands back a stored secret."""
    from backend.config import PROFILE_SECRET_REVEAL_ENABLED

    if not PROFILE_SECRET_REVEAL_ENABLED:
        raise HTTPException(status_code=403, detail="Secret reveal is disabled")

    profile = await _get_profile(db, user.tenant_id, profile_id)
    service = await _get_service(db, profile, service_id)
    logger.warning("Service secret revealed for profile %s by %s", profile.slug, user.email)
    return ProfileServiceSecretResponse(
        token=decrypt_secret(service.token_encrypted),
        credentials=decrypt_json(service.credentials_encrypted),
    )


@router.post("/{profile_id}/services/{service_id}/health-check", response_model=ProfileServiceResponse)
async def run_health_check(
    profile_id: UUID,
    service_id: UUID,
    user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """Probe the service endpoint and record the outcome on the row."""
    profile = await _get_profile(db, user.tenant_id, profile_id)
    service = await _get_service(db, profile, service_id)
    target = validate_health_check_url(service.api_base_url, service.health_check_url)
    await check_service_health(service, target)
    await db.commit()
    return _service_response(service)


@router.get("/{profile_id}/config", response_model=List[ProfileConfigItemResponse])
async def list_config(
    profile_id: UUID,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(db, user.tenant_id, profile_id)
    return [_config_response(item) for item in profile.config_items or []]


@router.post(
    "/{profile_id}/config",
    response_model=ProfileConfigItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_config_item(
    profile_id: UUID,
    payload: ProfileConfigItemCreate,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(db, user.tenant_id, profile_id)
    for existing in profile.config_items or []:
        if existing.key == payload.key:
            raise HTTPException(status_code=409, detail=f"Config key '{payload.key}' already exists")

    item = ProfileConfigItem(
        profile_id=profile.id,
        tenant_id=user.tenant_id,
        key=payload.key,
        value=encrypt_secret(payload.value) if payload.is_secret else payload.value,
        description=payload.description,
        value_type=payload.value_type,
        is_secret=payload.is_secret,
        tags=payload.tags,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return _config_response(item)


@router.patch("/{profile_id}/config/{item_id}", response_model=ProfileConfigItemResponse)
@router.put("/{profile_id}/config/{item_id}", response_model=ProfileConfigItemResponse, include_in_schema=False)
async def update_config_item(
    profile_id: UUID,
    item_id: UUID,
    payload: ProfileConfigItemUpdate,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(db, user.tenant_id, profile_id)
    item = await _get_config_item(db, profile, item_id)
    data = payload.model_dump(exclude_unset=True)

    # Whether the value is encrypted depends on `is_secret` after the update, so
    # re-read the flag rather than deciding from the patch alone.
    now_secret = data.get("is_secret", item.is_secret)
    if "value" in data:
        item.value = encrypt_secret(data["value"]) if now_secret else data["value"]
    if "value_type" in data and data["value_type"]:
        cleaned = data["value_type"].strip().lower()
        if cleaned not in {"string", "number", "boolean", "json"}:
            raise HTTPException(
                status_code=422,
                detail="value_type must be string, number, boolean or json",
            )
        item.value_type = cleaned
    if "description" in data:
        item.description = data["description"]
    if "is_secret" in data:
        item.is_secret = data["is_secret"]
        # Flipping a value to secret must encrypt what is already stored, not
        # leave plaintext behind in the column.
        if data["is_secret"] and item.value and item.value is not None:
            plaintext = decrypt_secret(item.value)
            if plaintext is not None:
                item.value = encrypt_secret(plaintext)
    if "tags" in data and data["tags"] is not None:
        item.tags = [tag.strip() for tag in data["tags"] if tag and tag.strip()]

    await db.commit()
    return _config_response(item)


@router.delete("/{profile_id}/config/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_config_item(
    profile_id: UUID,
    item_id: UUID,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    profile = await _get_profile(db, user.tenant_id, profile_id)
    item = await _get_config_item(db, profile, item_id)
    await db.delete(item)
    await db.commit()
