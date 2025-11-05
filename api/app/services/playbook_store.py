"""Services for managing playbook metadata and execution."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.playbook import Playbook
from app.schemas.playbook import PlaybookRead, PlaybookRunMatch, PlaybookRunResult
from app.utils.sigma import iter_jsonl_records, load_sigma_rules, record_matches_selection

settings = get_settings()


class PlaybookNotFoundError(Exception):
    """Raised when a playbook is not found."""


async def list_playbooks(session: AsyncSession) -> list[PlaybookRead]:
    result = await session.execute(select(Playbook))
    playbooks = result.scalars().all()
    return [PlaybookRead.model_validate(pb) for pb in playbooks]


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

    rules = load_sigma_rules(rule_full_path)
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
    return PlaybookRunResult(
        playbook_id=playbook.id,
        matches=matches,
        total_records=len(records),
        matched_count=matched_count,
        execution_notes="Local execution against JSONL sample data",
    )
