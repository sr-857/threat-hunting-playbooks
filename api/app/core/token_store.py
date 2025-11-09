from __future__ import annotations

import asyncio
import time
from typing import Optional

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings


class RefreshTokenStore:
    """Persist and validate refresh tokens using Redis with in-memory fallback."""

    def __init__(self) -> None:
        self._redis: Redis | None = None
        self._fallback = False
        self._memory: dict[str, tuple[str, float]] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _key(prefix: str, jti: str) -> str:
        return f"{prefix}{jti}"

    async def _get_redis(self) -> Optional[Redis]:
        settings = get_settings()
        redis_url = settings.redis_url
        if redis_url.startswith("memory://"):
            self._fallback = True
            return None

        if self._fallback:
            return None

        if self._redis is None:
            self._redis = Redis.from_url(redis_url, encoding="utf-8", decode_responses=True)

        try:
            await self._redis.ping()
        except RedisError:
            if self._redis is not None:
                await self._redis.close()
            self._redis = None
            self._fallback = True
            return None

        return self._redis

    def _cleanup_memory(self) -> None:
        now = time.monotonic()
        expired = [jti for jti, (_, exp) in self._memory.items() if exp <= now]
        for jti in expired:
            self._memory.pop(jti, None)

    async def store(self, jti: str, subject: str, ttl_seconds: int) -> None:
        ttl = max(ttl_seconds, 1)
        settings = get_settings()
        prefix = settings.redis_refresh_prefix.rstrip(":") + ":"

        client = await self._get_redis()
        if client is not None:
            await client.set(self._key(prefix, jti), subject, ex=ttl)
            return

        async with self._lock:
            self._cleanup_memory()
            self._memory[jti] = (subject, time.monotonic() + ttl)

    async def revoke(self, jti: str) -> None:
        settings = get_settings()
        prefix = settings.redis_refresh_prefix.rstrip(":") + ":"

        client = await self._get_redis()
        if client is not None:
            await client.delete(self._key(prefix, jti))
            return

        async with self._lock:
            self._cleanup_memory()
            self._memory.pop(jti, None)

    async def is_active(self, jti: str) -> bool:
        settings = get_settings()
        prefix = settings.redis_refresh_prefix.rstrip(":") + ":"

        client = await self._get_redis()
        if client is not None:
            return await client.exists(self._key(prefix, jti)) == 1

        async with self._lock:
            self._cleanup_memory()
            return jti in self._memory

    async def validate(self, jti: str, subject: str) -> bool:
        settings = get_settings()
        prefix = settings.redis_refresh_prefix.rstrip(":") + ":"

        client = await self._get_redis()
        if client is not None:
            value = await client.get(self._key(prefix, jti))
            return value == subject

        async with self._lock:
            self._cleanup_memory()
            data = self._memory.get(jti)
            if data is None:
                return False
            stored_subject, _ = data
            return stored_subject == subject
