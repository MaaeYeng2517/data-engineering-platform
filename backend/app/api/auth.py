"""Authentication API endpoints."""
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.utils.time import utcnow
from backend.app.dependencies import get_current_user, sync_admin_role
from backend.app.models.user import User
from backend.app.schemas import TokenResponse, UserCreate, UserLogin, UserResponse, UserUpdate
from backend.app.security import (
    CSRF_COOKIE_NAME,
    REFRESH_TOKEN_COOKIE_NAME,
    clear_auth_cookies,
    create_access_token,
    create_csrf_token,
    create_refresh_token,
    decode_token,
    set_auth_cookies,
    verify_csrf_token,
    verify_password,
)
from backend.config import COOKIE_SAMESITE, COOKIE_SECURE
from backend.database import get_db

router = APIRouter()


def _token_pair(user: User) -> tuple[str, str, str]:
    payload = {
        "user_id": str(user.id),
        "tenant_id": str(user.tenant_id),
        "email": user.email,
        "role": user.role.value,
    }
    return create_access_token(payload), create_refresh_token(payload), create_csrf_token()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    from backend.app.services.onboarding import activate_account

    email = user_data.email.strip().lower()
    existing = await db.execute(select(User.id).where(User.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    activated = await activate_account(
        db,
        email=email,
        password=user_data.password,
        full_name=user_data.full_name,
        plan_code="free",
        data={"source": "registration"},
    )
    user = activated.user

    access_token, refresh_token, csrf_token = _token_pair(user)
    set_auth_cookies(response, access_token, refresh_token, csrf_token)
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
        csrf_token=csrf_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    email = credentials.email.strip().lower()
    result = await db.execute(
        select(User)
        .options(selectinload(User.tenant))
        .where(User.email == email)
    )
    user = result.scalar_one_or_none()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active or not user.tenant or not user.tenant.is_active:
        raise HTTPException(status_code=403, detail="Account or workspace is disabled")

    await sync_admin_role(user)
    await db.commit()
    access_token, refresh_token, csrf_token = _token_pair(user)
    set_auth_cookies(response, access_token, refresh_token, csrf_token)
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
        csrf_token=csrf_token,
    )


@router.post("/logout")
async def logout(response: Response):
    clear_auth_cookies(response)
    return {"message": "Logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    response: Response,
    refresh_token_value: str | None = Cookie(None, alias=REFRESH_TOKEN_COOKIE_NAME),
    db: AsyncSession = Depends(get_db),
):
    if not refresh_token_value:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    try:
        payload = decode_token(refresh_token_value, "refresh")
        user_id = payload.get("user_id")
        if not user_id:
            raise ValueError("Missing user_id")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    result = await db.execute(
        select(User)
        .options(selectinload(User.tenant))
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    if not user or not user.is_active or not user.tenant or not user.tenant.is_active:
        raise HTTPException(status_code=401, detail="User or workspace is inactive")
    await sync_admin_role(user)
    await db.commit()
    access_token, new_refresh_token, csrf_token = _token_pair(user)
    set_auth_cookies(response, access_token, new_refresh_token, csrf_token)
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
        csrf_token=csrf_token,
    )


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    update: UserUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if update.full_name is not None:
        user.full_name = update.full_name.strip() or None
    user.updated_at = utcnow()
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.get("/csrf-token")
async def csrf_token(
    response: Response,
    current: str | None = Cookie(None, alias=CSRF_COOKIE_NAME),
):
    token = current or create_csrf_token()
    response.set_cookie(
        CSRF_COOKIE_NAME,
        token,
        max_age=60 * 60,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        path="/",
    )
    return {"csrf_token": token}


@router.post("/verify-csrf")
async def verify_csrf(
    request: Request,
    current: str | None = Cookie(None, alias=CSRF_COOKIE_NAME),
):
    header = request.headers.get("X-CSRF-Token")
    if not verify_csrf_token(header, current):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    return {"valid": True}
