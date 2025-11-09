"""Authentication and user management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_session_dependency
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    revoke_refresh_token,
)
from app.schemas.user import Token, TokenRefreshRequest, UserRead
from app.services.user_store import UserNotFoundError, authenticate_user, get_user

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def _access_ttl_seconds() -> int:
    return settings.access_token_ttl_minutes * 60


def _refresh_ttl_seconds() -> int:
    return settings.refresh_token_ttl_minutes * 60


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    if not settings.auth_cookie_enabled:
        return

    response.set_cookie(
        key=settings.auth_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        max_age=_refresh_ttl_seconds(),
        path=f"{settings.api_prefix}/auth",
    )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session_dependency()),
) -> Token:
    user = await authenticate_user(session, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")

    refresh_token, _ = await create_refresh_token(subject=str(user.id))
    access_token = create_access_token(subject=str(user.id), roles=user.roles, is_superuser=user.is_superuser)

    _set_refresh_cookie(response, refresh_token)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        access_token_expires_in=_access_ttl_seconds(),
        refresh_token_expires_in=_refresh_ttl_seconds(),
    )


@router.get("/me", response_model=UserRead)
async def read_current_user(current_user: UserRead = Depends(get_current_active_user)) -> UserRead:
    return current_user


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: str,
    session: AsyncSession = Depends(get_session_dependency()),
) -> UserRead:
    try:
        user = await get_user(session, user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return user


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    payload: TokenRefreshRequest,
    response: Response,
    session: AsyncSession = Depends(get_session_dependency()),
) -> Token:
    try:
        refresh_payload = await decode_refresh_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    subject = refresh_payload.get("sub")
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token payload")

    try:
        user = await get_user(session, subject)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found") from exc

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")

    old_jti = refresh_payload.get("jti")

    refresh_token, _ = await create_refresh_token(subject=str(user.id))
    access_token = create_access_token(subject=str(user.id), roles=user.roles, is_superuser=user.is_superuser)

    if old_jti:
        await revoke_refresh_token(old_jti)

    _set_refresh_cookie(response, refresh_token)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        access_token_expires_in=_access_ttl_seconds(),
        refresh_token_expires_in=_refresh_ttl_seconds(),
    )
