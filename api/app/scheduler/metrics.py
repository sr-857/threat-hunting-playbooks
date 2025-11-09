"""Prometheus metrics helpers for Celery safeguards."""

from __future__ import annotations

from prometheus_client import Counter, Gauge

from app.core.config import get_settings


settings = get_settings()


_LOCK_ACQUIRE_TOTAL = Counter(
    "celery_lock_acquire_total",
    "Total attempts to acquire distributed locks",
    labelnames=("lock",),
)
_LOCK_ACQUIRE_CONTENTION = Counter(
    "celery_lock_contention_total",
    "Lock acquisition attempts that hit contention",
    labelnames=("lock",),
)
_LOCK_FALLBACK_TOTAL = Counter(
    "celery_lock_fallback_total",
    "Lock operations that required in-memory fallback",
    labelnames=("lock",),
)
_LOCK_RELEASE_TOTAL = Counter(
    "celery_lock_release_total",
    "Total lock release attempts",
    labelnames=("lock",),
)
_LOCK_RELEASE_FALLBACK = Counter(
    "celery_lock_release_fallback_total",
    "Lock releases performed via in-memory fallback",
    labelnames=("lock",),
)
_QUEUE_ENQUEUED_TOTAL = Counter(
    "celery_hunt_tasks_enqueued_total",
    "Total hunt tasks enqueued into Celery",
    labelnames=("source",),
)
_RECONCILE_BACKLOG = Gauge(
    "celery_hunt_reconcile_backlog",
    "Number of due hunts discovered during schedule reconciliation",
)
_DUPLICATE_SKIPS = Counter(
    "celery_hunt_duplicate_skips_total",
    "Hunt task executions skipped due to idempotency locks",
)


def _metrics_enabled() -> bool:
    return bool(settings.enable_metrics)


def _lock_label(name: str) -> str:
    parts = name.split(":")
    if len(parts) >= 2:
        return parts[1] or "default"
    return parts[0] or "default"


def record_lock_attempt(lock_name: str, acquired: bool, used_fallback: bool) -> None:
    if not _metrics_enabled():
        return
    label = _lock_label(lock_name)
    _LOCK_ACQUIRE_TOTAL.labels(label).inc()
    if not acquired:
        _LOCK_ACQUIRE_CONTENTION.labels(label).inc()
    if used_fallback:
        _LOCK_FALLBACK_TOTAL.labels(label).inc()


def record_lock_release(lock_name: str, used_fallback: bool) -> None:
    if not _metrics_enabled():
        return
    label = _lock_label(lock_name)
    _LOCK_RELEASE_TOTAL.labels(label).inc()
    if used_fallback:
        _LOCK_RELEASE_FALLBACK.labels(label).inc()


def record_queue_enqueued(count: int, source: str) -> None:
    if not _metrics_enabled() or count <= 0:
        return
    _QUEUE_ENQUEUED_TOTAL.labels(source).inc(count)


def record_reconcile_backlog(count: int) -> None:
    if not _metrics_enabled():
        return
    _RECONCILE_BACKLOG.set(count)


def record_duplicate_skip() -> None:
    if not _metrics_enabled():
        return
    _DUPLICATE_SKIPS.inc()
