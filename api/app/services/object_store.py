"""MinIO-backed object storage helpers with secure defaults."""

from __future__ import annotations

import mimetypes
from datetime import timedelta
from functools import lru_cache
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, Optional
from urllib.parse import urlparse
from uuid import uuid4

import structlog
from minio import Minio
from minio.commonconfig import ENABLED, VersioningConfig
from minio.error import S3Error

from app.core.config import get_settings

logger = structlog.get_logger(__name__)


class ObjectStoreError(RuntimeError):
    """Raised when object storage operations fail."""


class ObjectStoreDisabledError(ObjectStoreError):
    """Raised when attempting to use object storage while disabled."""


class ObjectStore:
    """High-level wrapper around MinIO with hardened defaults."""

    def __init__(self) -> None:
        self._settings = get_settings()
        self._enabled = bool(self._settings.minio_enabled)
        self._bucket = self._settings.minio_bucket.strip()
        self._prefix = self._settings.minio_artifact_prefix.strip("/")
        self._presign_ttl = int(self._settings.minio_presign_ttl_seconds)
        self._client: Optional[Minio] = None

        if self._enabled:
            self._client = self._build_client()
            self._ensure_bucket()

    @property
    def enabled(self) -> bool:
        return self._enabled and self._client is not None

    def _build_client(self) -> Minio:
        endpoint = self._settings.minio_endpoint
        parsed = urlparse(endpoint if "://" in endpoint else f"http://{endpoint}")
        host = parsed.netloc or parsed.path
        if not host:
            raise ObjectStoreError("Invalid MinIO endpoint configuration")

        secure = bool(self._settings.minio_secure)
        if parsed.scheme == "https":
            secure = True

        return Minio(
            host,
            access_key=self._settings.minio_access_key,
            secret_key=self._settings.minio_secret_key,
            secure=secure,
            region=self._settings.minio_region,
        )

    def _ensure_bucket(self) -> None:
        assert self._client is not None  # nosec - guarded by enabled check
        try:
            if not self._client.bucket_exists(self._bucket):
                self._client.make_bucket(self._bucket, location=self._settings.minio_region)
                logger.info("object_store.bucket_created", bucket=self._bucket)

            # Enforce private bucket by removing any existing policy.
            try:
                self._client.delete_bucket_policy(self._bucket)
            except S3Error as exc:  # noqa: PERF203 - small exception list
                if exc.code not in {"NoSuchBucketPolicy", "MethodNotAllowed"}:
                    raise

            # Enable versioning for better recovery from accidental overwrites.
            self._client.set_bucket_versioning(self._bucket, VersioningConfig(ENABLED))
        except S3Error as exc:  # pragma: no cover - depends on external service
            logger.error("object_store.bootstrap_failed", bucket=self._bucket, error=str(exc))
            raise ObjectStoreError("Failed to initialize MinIO bucket") from exc

    def put_file(
        self,
        path: Path,
        *,
        namespace: str | None = None,
        object_name: str | None = None,
        content_type: str | None = None,
        metadata: Optional[Dict[str, str]] = None,
    ) -> str:
        """Upload a local file to the configured bucket and return the object key."""

        if not self.enabled:
            raise ObjectStoreDisabledError("Object storage is disabled")
        if self._client is None:
            raise ObjectStoreError("Object storage client not initialized")
        if not path.is_file():
            raise FileNotFoundError(path)

        key = self._build_object_key(namespace, object_name or path.name)
        ctype = content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        meta = {k: str(v) for k, v in (metadata or {}).items() if v is not None}

        try:
            self._client.fput_object(
                self._bucket,
                key,
                str(path),
                content_type=ctype,
                metadata=meta or None,
            )
            return key
        except S3Error as exc:  # pragma: no cover - depends on external service
            logger.error("object_store.upload_failed", key=key, error=str(exc))
            raise ObjectStoreError(f"Failed to upload object {key}") from exc

    def presign(self, key: str, *, ttl_seconds: int | None = None) -> str:
        """Generate a presigned GET URL for the given object key."""

        if not self.enabled or self._client is None:
            raise ObjectStoreDisabledError("Object storage is disabled")

        validated_key = self._validate_key(key)
        ttl = int(ttl_seconds or self._presign_ttl)
        ttl = max(1, min(ttl, 7 * 24 * 60 * 60))  # MinIO presign limit: <=7 days

        try:
            return self._client.get_presigned_url(
                "GET",
                self._bucket,
                validated_key,
                expires=timedelta(seconds=ttl),
            )
        except S3Error as exc:  # pragma: no cover - depends on external service
            logger.error("object_store.presign_failed", key=validated_key, error=str(exc))
            raise ObjectStoreError(f"Failed to presign object {validated_key}") from exc

    def delete(self, key: str) -> None:
        """Remove an object from storage."""

        if not self.enabled or self._client is None:
            raise ObjectStoreDisabledError("Object storage is disabled")

        validated_key = self._validate_key(key)
        try:
            self._client.remove_object(self._bucket, validated_key)
        except S3Error as exc:  # pragma: no cover - depends on external service
            logger.error("object_store.delete_failed", key=validated_key, error=str(exc))
            raise ObjectStoreError(f"Failed to delete object {validated_key}") from exc

    def _build_object_key(self, namespace: str | None, name: str) -> str:
        segments: list[str] = []
        if self._prefix:
            segments.append(self._prefix)
        segments.extend(self._safe_segments(namespace) if namespace else [])

        if name:
            filename = self._safe_filename(name)
        else:
            filename = f"{uuid4().hex}"
        segments.append(filename)

        if not segments:
            raise ObjectStoreError("Object key resolved to an empty path")
        return "/".join(segments)

    def _safe_segments(self, value: str) -> Iterable[str]:
        parts = []
        for part in PurePosixPath(value).parts:
            if part in {"", ".", ".."}:
                continue
            parts.append(part)
        return parts

    def _safe_filename(self, name: str) -> str:
        parts = list(PurePosixPath(name).parts)
        if not parts:
            return f"{uuid4().hex}"
        suffix = Path(parts[-1]).suffix
        return f"{uuid4().hex}{suffix}" if suffix else f"{uuid4().hex}"

    def _validate_key(self, key: str) -> str:
        parts = list(PurePosixPath(key).parts)
        if not parts or any(part in {"", ".", ".."} for part in parts):
            raise ObjectStoreError("Invalid object key")
        return "/".join(parts)


@lru_cache(maxsize=1)
def get_object_store() -> ObjectStore:
    """Return a singleton ObjectStore instance."""

    return ObjectStore()


__all__ = ["ObjectStore", "ObjectStoreError", "ObjectStoreDisabledError", "get_object_store"]
