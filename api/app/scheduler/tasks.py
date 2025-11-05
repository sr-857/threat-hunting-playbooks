"""Celery tasks for executing hunts."""

from __future__ import annotations

import asyncio
from datetime import datetime
from uuid import UUID

import structlog

from app.db.session import AsyncSessionLocal
from app.scheduler.celery_app import celery_app
from app.services.playbook_store import execute_playbook_local, get_playbook
from app.services.schedule_store import (
    HuntScheduleNotFoundError,
    calculate_next_run,
    get_schedule,
    update_last_run,
)
from app.services.telemetry import record_hunt_execution, record_hunt_failure

logger = structlog.get_logger(__name__)


def _to_uuid(value: str | UUID | None) -> UUID | None:
    if value is None:
        return None
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


async def _run_playbook(playbook_id: UUID, schedule_id: UUID | None) -> dict[str, object]:
    trigger = "schedule" if schedule_id else "celery"
    async with AsyncSessionLocal() as session:
        try:
            playbook = await get_playbook(session, playbook_id)
        except Exception as exc:  # pragma: no cover - defensive
            record_hunt_failure(str(playbook_id), trigger, exc, str(schedule_id) if schedule_id else None)
            raise

        try:
            result = execute_playbook_local(playbook)
        except Exception as exc:
            record_hunt_failure(str(playbook_id), trigger, exc, str(schedule_id) if schedule_id else None)
            raise

        schedule_info = None
        if schedule_id is not None:
            try:
                schedule_info = await get_schedule(session, schedule_id)
            except HuntScheduleNotFoundError:
                logger.warning("schedule.missing", schedule_id=str(schedule_id))
                schedule_info = None

            next_run = None
            if schedule_info and schedule_info.enabled:
                next_run = calculate_next_run(schedule_info.cron_expression, datetime.utcnow())
            try:
                await update_last_run(session, schedule_id, datetime.utcnow(), next_run)
            except HuntScheduleNotFoundError:
                logger.warning("schedule.lost_before_update", schedule_id=str(schedule_id))

        telemetry_event = record_hunt_execution(
            playbook,
            result,
            trigger=trigger,
            schedule_id=str(schedule_id) if schedule_id else None,
            metadata={"source": "celery"},
        )

        return {
            "matched": result.matched_count,
            "total": result.total_records,
            "confidence": result.confidence,
            "summary": result.summary,
            "telemetry": telemetry_event,
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

    logger.info(
        "celery.hunt.start",
        playbook_id=str(real_playbook_id),
        schedule_id=str(real_schedule_id) if real_schedule_id else None,
    )
    try:
        response = _run_async(real_playbook_id, real_schedule_id)
        logger.info(
            "celery.hunt.completed",
            playbook_id=str(real_playbook_id),
            schedule_id=str(real_schedule_id) if real_schedule_id else None,
            matched=response.get("matched"),
            total=response.get("total"),
            confidence=response.get("confidence"),
        )
        return response
    except Exception as exc:  # pragma: no cover - propagate state to caller
        record_hunt_failure(
            str(real_playbook_id),
            "schedule" if real_schedule_id else "celery",
            exc,
            str(real_schedule_id) if real_schedule_id else None,
        )
        logger.exception(
            "celery.hunt.failed",
            playbook_id=str(real_playbook_id),
            schedule_id=str(real_schedule_id) if real_schedule_id else None,
        )
        raise
