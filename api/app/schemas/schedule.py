"""Pydantic schemas for hunt schedules."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HuntScheduleBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: str | None = None
    playbook_id: UUID
    cron_expression: str = Field(..., max_length=64)
    enabled: bool = True


class HuntScheduleCreate(HuntScheduleBase):
    pass


class HuntScheduleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    description: str | None = None
    cron_expression: str | None = Field(default=None, max_length=64)
    enabled: bool | None = None


class HuntScheduleRead(HuntScheduleBase):
    id: UUID
    last_run_at: datetime | None
    next_run_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
