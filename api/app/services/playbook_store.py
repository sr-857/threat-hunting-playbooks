"""Services for managing playbook metadata and execution."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from time import monotonic
from pathlib import Path
from typing import Iterable
from uuid import UUID

import structlog

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.models.playbook import Playbook
from app.schemas.playbook import PlaybookRead, PlaybookRunMatch, PlaybookRunResult
from app.utils.sigma import (
    SigmaValidationError,
    iter_jsonl_records,
    load_sigma_rules,
    record_matches_selection,
    validate_sigma_rules,
)

from app.services.object_store import (
    ObjectStoreError,
    ObjectStoreDisabledError,
    get_object_store,
)

_CACHE_TTL_SECONDS = 30.0
_playbook_cache: dict[str, object] = {"timestamp": 0.0, "data": None}

settings = get_settings()
logger = structlog.get_logger(__name__)


class PlaybookNotFoundError(Exception):
    """Raised when a playbook is not found."""


async def list_playbooks(
    session: AsyncSession,
    *,
    offset: int = 0,
    limit: int = 100,
) -> list[PlaybookRead]:
    offset = max(offset, 0)
    limit = max(limit, 1)

    now = monotonic()
    cached_data = _playbook_cache["data"]
    if (
        cached_data is not None
        and isinstance(cached_data, list)
        and now - float(_playbook_cache["timestamp"]) < _CACHE_TTL_SECONDS
    ):
        return cached_data[offset : offset + limit]

    query = select(Playbook).offset(offset).limit(limit)
    result = await session.execute(query)
    playbooks = result.scalars().all()
    records = [PlaybookRead.model_validate(pb) for pb in playbooks]

    # Refresh cache when fetching from the beginning to avoid partial caches.
    if offset == 0:
        _playbook_cache["timestamp"] = now
        _playbook_cache["data"] = records

    return records


async def get_playbook(session: AsyncSession, playbook_id: UUID) -> PlaybookRead:
    playbook = await session.get(Playbook, str(playbook_id))
    if playbook is None:
        raise PlaybookNotFoundError(f"Playbook {playbook_id} not found")
    return PlaybookRead.model_validate(playbook)


def execute_playbook_local(playbook: PlaybookRead) -> PlaybookRunResult:
    rule_full_path = settings.rules_root.joinpath(playbook.rule_path).resolve()
    data_full_path = settings.samples_root.joinpath(playbook.data_path).resolve()

    if not rule_full_path.exists():
        raise FileNotFoundError(f"Rule file not found: {rule_full_path}")
    if not data_full_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_full_path}")

    try:
        rules = load_sigma_rules(rule_full_path)
        validate_sigma_rules(rules)
    except (ValueError, SigmaValidationError) as exc:
        raise ValueError(f"Invalid Sigma rule file {rule_full_path}: {exc}") from exc
    records = list(iter_jsonl_records(data_full_path)) if playbook.data_format.lower() == "jsonl" else []
    if playbook.data_format.lower() != "jsonl":
        raise ValueError(f"Unsupported data format: {playbook.data_format}")

    matches: list[PlaybookRunMatch] = []
    for record in records:
        matched_rule_title: str | None = None
        for rule in rules:
            detection = rule.get("detection", {})
            selection = detection.get("selection", {})
            if selection and record_matches_selection(record, selection):
                matched_rule_title = rule.get("title")
                break
        matched = matched_rule_title is not None
        matches.append(
            PlaybookRunMatch(
                record=record,
                matched=matched,
                reason=f"Matched rule {matched_rule_title}" if matched else None,
            )
        )

    matched_count = sum(1 for result in matches if result.matched)
    total_records = len(records)
    confidence = matched_count / total_records if total_records else 0.0
    summary = f"{matched_count}/{total_records} records matched" if total_records else "No records processed"

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = settings.artifacts_root.joinpath("output", str(playbook.id))
    output_dir.mkdir(parents=True, exist_ok=True)
    artifact_file = output_dir.joinpath(f"result_{timestamp}.json")

    artifact_payload = {
        "playbook_id": str(playbook.id),
        "generated_at": timestamp,
        "summary": summary,
        "confidence": confidence,
        "matched_count": matched_count,
        "total_records": total_records,
        "notes": "Local execution against JSONL sample data",
        "matches": [match.model_dump() for match in matches],
    }
    artifact_file.write_text(json.dumps(artifact_payload, default=str), encoding="utf-8")

    artifact_paths: dict[str, str] = {"result": str(artifact_file)}
    _maybe_upload_artifact(artifact_file, playbook, timestamp, artifact_paths)

    return PlaybookRunResult(
        playbook_id=playbook.id,
        matches=matches,
        total_records=total_records,
        matched_count=matched_count,
        execution_notes="Local execution against JSONL sample data",
        summary=summary,
        confidence=confidence,
        artifact_paths=artifact_paths,
    )


def _maybe_upload_artifact(
    artifact_file: Path,
    playbook: PlaybookRead,
    timestamp: str,
    artifact_paths: dict[str, str],
) -> None:
    try:
        store = get_object_store()
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning(
            "playbook_store.object_store_unavailable", error=str(exc)
        )
        return

    if not store.enabled:
        return

    metadata = {
        "playbook_id": str(playbook.id),
        "generated_at": timestamp,
        "artifact_type": "playbook-result",
    }

    try:
        object_key = store.put_file(
            artifact_file,
            namespace=f"playbooks/{playbook.id}",
            object_name=artifact_file.name,
            metadata=metadata,
        )
        artifact_paths["result_object_key"] = object_key
        artifact_paths["result_presigned_url"] = store.presign(object_key)
    except ObjectStoreDisabledError:
        # Disabled after initialization; nothing to do.
        logger.debug("playbook_store.object_store_disabled")
    except ObjectStoreError as exc:  # pragma: no cover - external dependency
        logger.warning(
            "playbook_store.object_store_upload_failed",
            error=str(exc),
            playbook_id=str(playbook.id),
        )
