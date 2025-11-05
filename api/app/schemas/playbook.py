"""Pydantic schemas for playbook resources."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PlaybookBase(BaseModel):
    name: str
    description: str | None = None
    rule_path: str
    data_path: str
    data_format: str = "jsonl"
    tags: list[str] = []
    enabled: bool = True


class PlaybookRead(PlaybookBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PlaybookRunMatch(BaseModel):
    record: dict[str, Any]
    matched: bool
    reason: str | None = None


class PlaybookRunResult(BaseModel):
    playbook_id: UUID
    matches: list[PlaybookRunMatch]
    total_records: int
    matched_count: int
    execution_notes: str | None = None


class PlaybookRunResponse(BaseModel):
    playbook: PlaybookRead
    result: PlaybookRunResult
