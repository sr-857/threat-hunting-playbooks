"""Services for managing hunt schedules."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable
from uuid import UUID

from croniter import croniter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.schedule import HuntSchedule
from app.schemas.schedule import HuntScheduleCreate, HuntScheduleRead, HuntScheduleUpdate


class HuntScheduleNotFoundError(Exception):
    """Raised when a hunt schedule cannot be located."""


def calculate_next_run(cron_expression: str, base_time: datetime | None = None) -> datetime:
    base = base_time or datetime.utcnow()
    iterator = croniter(cron_expression, base)
    return iterator.get_next(datetime)


async def list_schedules(session: AsyncSession) -> list[HuntScheduleRead]:
    result = await session.execute(select(HuntSchedule))
    schedules = result.scalars().all()
    return [HuntScheduleRead.model_validate(item) for item in schedules]


async def get_schedule(session: AsyncSession, schedule_id: UUID) -> HuntScheduleRead:
    schedule = await session.get(HuntSchedule, str(schedule_id))
    if schedule is None:
        raise HuntScheduleNotFoundError(f"Schedule {schedule_id} not found")
    return HuntScheduleRead.model_validate(schedule)


async def create_schedule(session: AsyncSession, data: HuntScheduleCreate) -> HuntScheduleRead:
    base_time = datetime.utcnow()
    next_run = calculate_next_run(data.cron_expression, base_time)
    schedule = HuntSchedule(
        name=data.name,
        description=data.description,
        playbook_id=str(data.playbook_id),
        cron_expression=data.cron_expression,
        enabled=data.enabled,
        next_run_at=next_run,
    )
    session.add(schedule)
    await session.commit()
    await session.refresh(schedule)
    return HuntScheduleRead.model_validate(schedule)


async def update_schedule(
    session: AsyncSession,
    schedule_id: UUID,
    data: HuntScheduleUpdate,
) -> HuntScheduleRead:
    schedule = await session.get(HuntSchedule, str(schedule_id))
    if schedule is None:
        raise HuntScheduleNotFoundError(f"Schedule {schedule_id} not found")

    if data.name is not None:
        schedule.name = data.name
    if data.description is not None:
        schedule.description = data.description
    if data.cron_expression is not None:
        schedule.cron_expression = data.cron_expression
        schedule.next_run_at = calculate_next_run(schedule.cron_expression, datetime.utcnow())
    if data.enabled is not None:
        schedule.enabled = data.enabled

    schedule.updated_at = datetime.utcnow()
    await session.commit()
    await session.refresh(schedule)
    return HuntScheduleRead.model_validate(schedule)


async def delete_schedule(session: AsyncSession, schedule_id: UUID) -> None:
    schedule = await session.get(HuntSchedule, str(schedule_id))
    if schedule is None:
        raise HuntScheduleNotFoundError(f"Schedule {schedule_id} not found")
    await session.delete(schedule)
    await session.commit()


async def update_last_run(
    session: AsyncSession,
    schedule_id: UUID,
    last_run: datetime,
    next_run: datetime | None,
) -> None:
    schedule = await session.get(HuntSchedule, str(schedule_id))
    if schedule is None:
        raise HuntScheduleNotFoundError(f"Schedule {schedule_id} not found")
    schedule.last_run_at = last_run
    schedule.next_run_at = next_run
    await session.commit()
