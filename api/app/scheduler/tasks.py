"""Celery tasks for executing hunts."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from uuid import UUID

from app.scheduler.celery_app import celery_app
from app.db.session import AsyncSessionLocal
from app.services.playbook_store import get_playbook, execute_playbook_local
from app.services.schedule_store import (
    HuntScheduleNotFoundError,
    calculate_next_run,
    get_schedule,
    update_last_run,
)

logger = logging.getLogger(__name__)


def _to_uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


async def _run_playbook(playbook_id: UUID, schedule_id: UUID | None) -> dict[str, object]:
    async with AsyncSessionLocal() as session:
        playbook = await get_playbook(session, playbook_id)
        result = execute_playbook_local(playbook)

        schedule_info = None
        if schedule_id is not None:
            try:
                schedule_info = await get_schedule(session, schedule_id)
            except HuntScheduleNotFoundError:
                logger.warning("Schedule %s not found during post-run update", schedule_id)
                schedule_info = None

            next_run = None
            if schedule_info and schedule_info.enabled:
                next_run = calculate_next_run(schedule_info.cron_expression, datetime.utcnow())
            try:
                await update_last_run(session, schedule_id, datetime.utcnow(), next_run)
            except HuntScheduleNotFoundError:
                logger.warning("Schedule %s disappeared before updating last run", schedule_id)

        return {
            "matched": result.matched_count,
            "total": result.total_records,
            "schedule": schedule_info.model_dump() if schedule_info else None,
        }


def _run_async(playbook_id: UUID, schedule_id: UUID | None) -> dict[str, object]:
    return asyncio.run(_run_playbook(playbook_id, schedule_id))


@celery_app.task(name="run_playbook_task")
def run_playbook_task(playbook_id: str, schedule_id: str | None = None) -> dict[str, object]:
    """Execute a playbook and optionally update schedule metadata."""

    real_playbook_id = _to_uuid(playbook_id)
    real_schedule_id = _to_uuid(schedule_id)
    assert real_playbook_id is not None, "playbook_id is required"

    logger.info("Executing playbook %s (schedule=%s)", real_playbook_id, real_schedule_id)
    return _run_async(real_playbook_id, real_schedule_id)
