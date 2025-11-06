"""Services for managing application users."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserAlreadyExistsError(RuntimeError):
    """Raised when attempting to create a user that already exists."""


class UserNotFoundError(RuntimeError):
    """Raised when the requested user cannot be located."""


async def get_user(session: AsyncSession, user_id: str) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise UserNotFoundError(f"User {user_id} not found")
    return user


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email.lower()))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, data: UserCreate, *, as_superuser: bool = False) -> User:
    email = data.email.lower()
    existing = await get_user_by_email(session, email)
    if existing is not None:
        raise UserAlreadyExistsError(f"User with email {email} already exists")

    user = User(
        email=email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password),
        roles=data.roles,
        is_active=data.is_active,
        is_superuser=as_superuser or data.is_superuser,
    )
    session.add(user)
    try:
        await session.commit()
    except IntegrityError as exc:  # pragma: no cover - depends on DB state
        await session.rollback()
        raise UserAlreadyExistsError(f"User with email {email} already exists") from exc
    await session.refresh(user)
    return user


async def update_user(session: AsyncSession, user_id: str, data: UserUpdate) -> User:
    user = await get_user(session, user_id)
    if data.full_name is not None:
        user.full_name = data.full_name
    if data.roles is not None:
        user.roles = data.roles
    if data.is_active is not None:
        user.is_active = data.is_active
    if data.is_superuser is not None:
        user.is_superuser = data.is_superuser
    if data.password:
        user.hashed_password = hash_password(data.password)

    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(session, email.lower())
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def ensure_initial_superuser(session: AsyncSession, email: str, password: str) -> User:
    existing = await get_user_by_email(session, email)
    if existing:
        if not existing.is_superuser:
            existing.is_superuser = True
            if "admin" not in existing.roles:
                existing.roles = list({*existing.roles, "admin"})
            await session.commit()
            await session.refresh(existing)
        return existing

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name="Administrator",
        roles=["admin"],
        is_active=True,
        is_superuser=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
