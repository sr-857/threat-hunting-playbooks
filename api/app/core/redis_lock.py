from __future__ import annotations

import asyncio
import time
from typing import Optional

import structlog
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings
from app.scheduler.metrics import record_lock_attempt, record_lock_release


logger = structlog.get_logger(__name__)


class _RedisLockManager:
    """Coordinate distributed locks with Redis and a memory fallback."""

    def __init__(self) -> None:
        self._redis: Redis | None = None
        self._fallback = False
        self._memory: dict[str, float] = {}
        self._lock = asyncio.Lock()

    async def _get_client(self) -> Optional[Redis]:
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
        except RedisError as exc:  # pragma: no cover - depends on environment
            logger.warning("redis.lock.ping_failed", error=str(exc))
            if self._redis is not None:
                await self._redis.close()
            self._redis = None
            self._fallback = True
            return None

        return self._redis

    async def acquire(self, key: str, ttl_seconds: int) -> bool:
        ttl = max(1, int(ttl_seconds))
        client = await self._get_client()
        fallback_used = client is None or self._fallback
        if client is not None:
            try:
                acquired = bool(await client.set(key, "1", nx=True, ex=ttl))
                record_lock_attempt(key, acquired, False)
                return acquired
            except RedisError as exc:  # pragma: no cover - depends on redis availability
                logger.warning("redis.lock.acquire_failed", key=key, error=str(exc))
                self._fallback = True
                client = None
                fallback_used = True

        async with self._lock:
            self._cleanup_memory()
            if key in self._memory:
                acquired = False
            else:
                self._memory[key] = time.monotonic() + ttl
                acquired = True
        record_lock_attempt(key, acquired, fallback_used)
        return acquired

    async def release(self, key: str) -> None:
        client = await self._get_client()
        fallback_used = client is None or self._fallback
        if client is not None:
            try:
                await client.delete(key)
                record_lock_release(key, False)
                return
            except RedisError as exc:  # pragma: no cover - depends on redis availability
                logger.warning("redis.lock.release_failed", key=key, error=str(exc))
                self._fallback = True
                fallback_used = True

        async with self._lock:
            self._cleanup_memory()
            self._memory.pop(key, None)
        record_lock_release(key, fallback_used)

    def _cleanup_memory(self) -> None:
        now = time.monotonic()
        expired = [lock for lock, expiry in self._memory.items() if expiry <= now]
        for lock in expired:
            self._memory.pop(lock, None)


_LOCK_MANAGER = _RedisLockManager()


def _normalized_key(name: str) -> str:
    settings = get_settings()
    prefix = settings.task_lock_prefix.rstrip(":")
    base = name.lstrip(":")
    if prefix:
        return f"{prefix}:{base}"
    return base


async def acquire_lock_async(name: str, ttl_seconds: Optional[int] = None) -> bool:
    settings = get_settings()
    ttl = ttl_seconds if ttl_seconds is not None else settings.task_lock_ttl_seconds
    key = _normalized_key(name)
    return await _LOCK_MANAGER.acquire(key, ttl)


async def release_lock_async(name: str) -> None:
    key = _normalized_key(name)
    await _LOCK_MANAGER.release(key)


def acquire_lock(name: str, ttl_seconds: Optional[int] = None) -> bool:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(acquire_lock_async(name, ttl_seconds))
    else:  # pragma: no cover - not expected in sync contexts
        if loop.is_running():
            raise RuntimeError("acquire_lock cannot be called from an active event loop; use acquire_lock_async instead")
        return loop.run_until_complete(acquire_lock_async(name, ttl_seconds))


def release_lock(name: str) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(release_lock_async(name))
    else:  # pragma: no cover - not expected in sync contexts
        if loop.is_running():
            raise RuntimeError("release_lock cannot be called from an active event loop; use release_lock_async instead")
        loop.run_until_complete(release_lock_async(name))
