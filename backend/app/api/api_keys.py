"""API key management endpoints."""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.utils.time import utcnow
from backend.app.dependencies import require_platform_user
from backend.app.models.api_key import ApiKey, ApiUsageLog
from backend.app.models.user import User
from backend.app.schemas import (
    ApiKeyCreate,
    ApiKeyCreateResponse,
    ApiKeyResponse,
    ApiUsageLogResponse,
)
from backend.app.security import generate_api_key
from backend.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=ApiKeyCreateResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_api_key(
    payload: ApiKeyCreate,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    plain_key, key_prefix, key_hash = generate_api_key()
    api_key = ApiKey(
        user_id=user.id,
        tenant_id=user.tenant_id,
        name=payload.name.strip(),
        key_prefix=key_prefix,
        key_hash=key_hash,
        scopes=[scope.value for scope in payload.scopes],
        expires_at=payload.expires_at,
        is_active=True,
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    logger.info("Created API key %s for tenant %s", api_key.id, api_key.tenant_id)
    return ApiKeyCreateResponse(api_key=ApiKeyResponse.model_validate(api_key), plain_key=plain_key)


@router.get("", response_model=List[ApiKeyResponse])
@router.get("/", response_model=List[ApiKeyResponse], include_in_schema=False)
async def list_api_keys(
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey)
        .where(ApiKey.user_id == user.id)
        .order_by(ApiKey.created_at.desc())
    )
    return result.scalars().all()


@router.get("/usage", response_model=List[ApiUsageLogResponse])
async def list_usage(
    limit: int = 50,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiUsageLog)
        .where(ApiUsageLog.user_id == user.id)
        .order_by(ApiUsageLog.created_at.desc())
        .limit(max(1, min(limit, 200)))
    )
    return result.scalars().all()


@router.get("/usage/summary")
async def usage_summary(
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    total = await db.execute(
        select(func.count(ApiUsageLog.id)).where(ApiUsageLog.user_id == user.id)
    )
    today_start = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today = await db.execute(
        select(func.count(ApiUsageLog.id)).where(
            ApiUsageLog.user_id == user.id,
            ApiUsageLog.created_at >= today_start,
        )
    )
    return {"total_calls": total.scalar() or 0, "calls_today": today.scalar() or 0}


@router.delete("/{api_key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    api_key_id: str,
    user: User = Depends(require_platform_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == api_key_id, ApiKey.user_id == user.id)
    )
    api_key = result.scalar_one_or_none()
    if api_key is None:
        raise HTTPException(status_code=404, detail="API key not found")
    api_key.is_active = False
    api_key.revoked_at = utcnow()
    await db.commit()