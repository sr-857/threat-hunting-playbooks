"""Telemetry utilities for hunt execution monitoring."""

from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from time import monotonic

import structlog
from prometheus_client import Counter, Gauge

from app.core.config import get_settings
from app.schemas.playbook import PlaybookRead, PlaybookRunResult
from app.services.notifiers import notify_email, notify_pagerduty, notify_slack, notify_teams

_CACHE_TTL_SECONDS = 10.0
_cache: dict[str, dict[str, Any]] = {
    "events": {"timestamp": 0.0, "data": []},
    "alerts": {"timestamp": 0.0, "data": []},
}

settings = get_settings()
logger = structlog.get_logger(__name__)

HUNT_RUNS = Counter(
    "hunt_runs_total",
    "Total hunts executed",
    labelnames=("playbook_id", "trigger", "status"),
)
HUNT_ALERTS = Counter(
    "hunt_alerts_total",
    "Number of hunts exceeding confidence thresholds",
    labelnames=("playbook_id", "severity"),
)
HUNT_FAILURES = Counter(
    "hunt_failures_total",
    "Total hunts that failed to execute",
    labelnames=("playbook_id", "trigger"),
)
HUNT_CONFIDENCE = Gauge(
    "hunt_confidence_ratio",
    "Matched record ratio for the latest hunt execution",
    labelnames=("playbook_id",),
)


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _telemetry_directory() -> Path:
    path = settings.artifacts_root.joinpath("telemetry")
    path.mkdir(parents=True, exist_ok=True)
    return path


def _append_event(filename: str, event: dict[str, Any]) -> None:
    path = _telemetry_directory().joinpath(filename)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, default=str) + "\n")


def _read_jsonl(path: Path, limit: int) -> list[dict[str, Any]]:
    if not path.exists() or limit <= 0:
        return []
    buffer: deque[str] = deque(maxlen=limit)
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            buffer.append(line.strip())
    events: list[dict[str, Any]] = []
    for entry in buffer:
        if not entry:
            continue
        try:
            events.append(json.loads(entry))
        except json.JSONDecodeError:
            logger.warning("telemetry.invalid_entry", entry=entry)
    return events


def _get_cached(name: str, limit: int) -> list[dict[str, Any]] | None:
    cache_entry = _cache.get(name)
    if not cache_entry:
        return None
    if monotonic() - float(cache_entry["timestamp"]) > _CACHE_TTL_SECONDS:
        return None
    data = cache_entry.get("data") or []
    if len(data) >= limit:
        return data[:limit]
    return None


def _store_cache(name: str, data: list[dict[str, Any]]) -> None:
    _cache[name] = {
        "timestamp": monotonic(),
        "data": data,
    }


def list_hunt_events(limit: int = 100) -> list[dict[str, Any]]:
    """Return the most recent hunt execution/failure events."""

    cached = _get_cached("events", limit)
    if cached is not None:
        return cached

    events = _read_jsonl(_telemetry_directory().joinpath("hunt_events.jsonl"), limit)
    _store_cache("events", events)
    return events


def list_hunt_alerts(limit: int = 100) -> list[dict[str, Any]]:
    """Return the most recent hunt alerts."""

    cached = _get_cached("alerts", limit)
    if cached is not None:
        return cached

    alerts = _read_jsonl(_telemetry_directory().joinpath("hunt_alerts.jsonl"), limit)
    _store_cache("alerts", alerts)
    return alerts


def record_hunt_execution(
    playbook: PlaybookRead,
    result: PlaybookRunResult,
    trigger: str,
    schedule_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Persist telemetry for a successful hunt execution."""

    confidence = 0.0
    if result.total_records:
        confidence = result.matched_count / result.total_records

    event: dict[str, Any] = {
        "type": "hunt_execution",
        "timestamp": _timestamp(),
        "playbook_id": str(playbook.id),
        "trigger": trigger,
        "schedule_id": schedule_id,
        "matched_count": result.matched_count,
        "total_records": result.total_records,
        "confidence": round(confidence, 4),
        "notes": result.execution_notes,
        "metadata": metadata or {},
    }

    logger.info("hunt.execution", **event)
    _append_event("hunt_events.jsonl", event)
    _cache["events"]["timestamp"] = 0.0

    if settings.enable_metrics:
        HUNT_RUNS.labels(str(playbook.id), trigger, "success").inc()
        HUNT_CONFIDENCE.labels(str(playbook.id)).set(confidence)

    if confidence >= settings.alert_confidence_threshold:
        record_hunt_alert(playbook, confidence, trigger, schedule_id)

    return event


def record_hunt_failure(
    playbook_id: str,
    trigger: str,
    error: Exception,
    schedule_id: str | None = None,
) -> None:
    """Persist telemetry for a failed hunt."""

    event: dict[str, Any] = {
        "type": "hunt_failure",
        "timestamp": _timestamp(),
        "playbook_id": playbook_id,
        "trigger": trigger,
        "schedule_id": schedule_id,
        "error": repr(error),
    }
    logger.error("hunt.failure", **event)
    _append_event("hunt_events.jsonl", event)
    _cache["events"]["timestamp"] = 0.0

    if settings.enable_metrics:
        HUNT_FAILURES.labels(playbook_id, trigger).inc()


def record_hunt_alert(
    playbook: PlaybookRead,
    confidence: float,
    trigger: str,
    schedule_id: str | None = None,
) -> None:
    """Persist an alert-worthy hunt execution."""

    event: dict[str, Any] = {
        "type": "hunt_alert",
        "timestamp": _timestamp(),
        "playbook_id": str(playbook.id),
        "trigger": trigger,
        "schedule_id": schedule_id,
        "confidence": round(confidence, 4),
        "threshold": settings.alert_confidence_threshold,
    }

    logger.warning("hunt.alert", **event)
    _append_event("hunt_alerts.jsonl", event)
    _cache["alerts"]["timestamp"] = 0.0

    if settings.enable_metrics:
        HUNT_ALERTS.labels(str(playbook.id), "high").inc()

    summary = (
        f"Hunt {playbook.name} ({playbook.id}) exceeded the confidence threshold "
        f"({confidence:.2%} ≥ {settings.alert_confidence_threshold:.2%})."
    )
    details = [
        summary,
        f"Trigger: {trigger}",
        f"Schedule ID: {schedule_id or '—'}",
        f"Tags: {', '.join(playbook.tags) if playbook.tags else 'none'}",
    ]
    body = "\n".join(details)

    notify_slack({"text": body})
    notify_teams({"text": body})
    notify_pagerduty(summary=summary, severity="critical", source=str(playbook.id))
    notify_email(subject=f"Hunt alert: {playbook.name}", body=body)
