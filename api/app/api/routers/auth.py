"""Authentication and user management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_active_user, get_session_dependency
from app.core.security import create_access_token
from app.schemas.user import Token, UserRead
from app.services.user_store import UserNotFoundError, authenticate_user, get_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_session_dependency()),
) -> Token:
    user = await authenticate_user(session, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect credentials")

    token = create_access_token(subject=str(user.id), roles=user.roles, is_superuser=user.is_superuser)
    return Token(access_token=token)


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
