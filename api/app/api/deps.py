"""Common FastAPI dependencies."""

from collections.abc import AsyncGenerator, Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.models.user import User
from app.services.user_store import UserNotFoundError, get_user

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


def get_session_dependency() -> Callable[[], AsyncGenerator[AsyncSession, None]]:
    async def dependency() -> AsyncGenerator[AsyncSession, None]:
        async with AsyncSessionLocal() as session:
            yield session

    return dependency


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    try:
        payload = decode_access_token(token)
    except ValueError as exc:  # pragma: no cover - auth failure
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    subject = payload.get("sub")
    if subject is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    try:
        user = await get_user(session, subject)
    except UserNotFoundError as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found") from exc

    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def require_roles(required_roles: set[str]) -> Callable[[User], User]:
    async def dependency(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.is_superuser:
            return current_user
        if not required_roles.intersection(set(current_user.roles or [])):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges")
        return current_user

    return dependency
