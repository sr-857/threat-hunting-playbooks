"""Security utilities for password hashing and token management."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Any

import structlog
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.exc import MissingBackendError

from app.core.config import get_settings
from app.core.token_store import RefreshTokenStore

settings = get_settings()
logger = structlog.get_logger(__name__)

_PRIMARY_CONTEXT = CryptContext(schemes=["argon2", "bcrypt_sha256"], deprecated="auto")
try:
    _HAS_ARGON2 = _PRIMARY_CONTEXT.handler("argon2").has_backend()
except MissingBackendError:  # pragma: no cover - depends on optional dependency
    _HAS_ARGON2 = False

if not _HAS_ARGON2:
    logger.warning("argon2 backend unavailable; falling back to bcrypt_sha256 hashing")
    pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")
else:
    pwd_context = _PRIMARY_CONTEXT

_REFRESH_STORE: RefreshTokenStore | None = None


def _refresh_store() -> RefreshTokenStore:
    global _REFRESH_STORE
    if _REFRESH_STORE is None:
        _REFRESH_STORE = RefreshTokenStore()
    return _REFRESH_STORE


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def _base_claims(subject: str, expires_delta: timedelta, *, jti: str | None = None) -> dict[str, Any]:
    expire = datetime.now(timezone.utc) + expires_delta
    claims: dict[str, Any] = {"sub": subject, "exp": expire}
    if settings.jwt_issuer:
        claims["iss"] = settings.jwt_issuer
    if jti is not None:
        claims["jti"] = jti
    return claims


def _jwt_algorithm() -> str:
    return settings.jwt_algorithm or "HS256"


def create_access_token(
    subject: str,
    *,
    expires_delta: timedelta | None = None,
    **claims: Any,
) -> str:
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.access_token_ttl_minutes)
    payload = _base_claims(subject, expires_delta)
    payload.update(claims)
    return jwt.encode(payload, settings.secret_key, algorithm=_jwt_algorithm())


async def create_refresh_token(subject: str) -> tuple[str, str]:
    expires_delta = timedelta(minutes=settings.refresh_token_ttl_minutes)
    jti = token_urlsafe(16)
    payload = _base_claims(subject, expires_delta, jti=jti)
    token = jwt.encode(payload, settings.secret_key, algorithm=_jwt_algorithm())
    await _refresh_store().store(jti, subject, int(expires_delta.total_seconds()))
    return token, jti


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[_jwt_algorithm()],
            issuer=settings.jwt_issuer,
            options={"verify_iss": settings.jwt_issuer is not None},
        )
    except JWTError as exc:  # pragma: no cover - jose already tested upstream
        raise ValueError("Invalid token") from exc
    return payload


async def decode_refresh_token(token: str, *, subject: str | None = None) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[_jwt_algorithm()],
            issuer=settings.jwt_issuer,
            options={"verify_iss": settings.jwt_issuer is not None},
        )
    except JWTError as exc:
        raise ValueError("Invalid refresh token") from exc

    token_subject = payload.get("sub")
    if subject is not None and token_subject != subject:
        raise ValueError("Refresh token subject mismatch")

    jti = payload.get("jti")
    if jti is None:
        raise ValueError("Refresh token missing identifier")

    if not await _refresh_store().validate(jti, token_subject):
        raise ValueError("Refresh token revoked or expired")

    return payload


async def revoke_refresh_token(jti: str) -> None:
    logger.debug("revoking refresh token", jti=jti)
    await _refresh_store().revoke(jti)
