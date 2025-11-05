"""Telemetry utilities for hunt execution monitoring."""

from __future__ import annotations

import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog
from prometheus_client import Counter, Gauge

from app.core.config import get_settings
from app.schemas.playbook import PlaybookRead, PlaybookRunResult

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


def list_hunt_events(limit: int = 100) -> list[dict[str, Any]]:
    """Return the most recent hunt execution/failure events."""

    return _read_jsonl(_telemetry_directory().joinpath("hunt_events.jsonl"), limit)


def list_hunt_alerts(limit: int = 100) -> list[dict[str, Any]]:
    """Return the most recent hunt alerts."""

    return _read_jsonl(_telemetry_directory().joinpath("hunt_alerts.jsonl"), limit)


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

    if settings.enable_metrics:
        HUNT_ALERTS.labels(str(playbook.id), "high").inc()
