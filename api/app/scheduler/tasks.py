"""Celery tasks for executing hunts."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from uuid import UUID

import structlog
from celery import Task
from celery.exceptions import Ignore
from celery.signals import worker_ready
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.scheduler.celery_app import celery_app
from app.core.config import get_settings
from app.core.redis_lock import acquire_lock_async, release_lock_async
from app.models.schedule import HuntSchedule
from app.scheduler.metrics import (
    record_duplicate_skip,
    record_queue_enqueued,
    record_reconcile_backlog,
)
from app.services.playbook_store import execute_playbook_local, get_playbook
from app.services.schedule_store import (
    HuntScheduleNotFoundError,
    calculate_next_run,
    get_schedule,
    update_last_run,
)
from app.services.telemetry import record_hunt_execution, record_hunt_failure

logger = structlog.get_logger(__name__)
settings = get_settings()


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


MAX_CATCHUP_RUNS = 5


def _as_utc_naive(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


async def _reconcile_schedules_async(now: datetime | None = None) -> None:
    current_time = _as_utc_naive(now) or datetime.utcnow()
    due_runs: list[tuple[str, str]] = []

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(HuntSchedule).where(HuntSchedule.enabled.is_(True))
        )
        schedules = list(result.scalars())

        for schedule in schedules:
            next_run = _as_utc_naive(schedule.next_run_at)

            if next_run is None:
                seed_time = current_time - timedelta(minutes=1)
                next_run = calculate_next_run(schedule.cron_expression, seed_time)

            catchups = 0
            while next_run is not None and next_run <= current_time and catchups < MAX_CATCHUP_RUNS:
                due_runs.append((str(schedule.playbook_id), str(schedule.id)))
                catchups += 1
                next_run = calculate_next_run(schedule.cron_expression, next_run)

            schedule.next_run_at = next_run

        await session.commit()

    record_reconcile_backlog(len(due_runs))
    if due_runs:
        logger.info("scheduler.reconcile.enqueued", count=len(due_runs))
        record_queue_enqueued(len(due_runs), "reconcile")
        for playbook_id, schedule_id in due_runs:
            enqueue_run_playbook(playbook_id, schedule_id, source="reconcile")
    else:
        logger.info("scheduler.reconcile.no_due_runs")


def reconcile_schedules(now: datetime | None = None) -> None:
    try:
        asyncio.run(_reconcile_schedules_async(now=now))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_reconcile_schedules_async(now=now))
        finally:
            loop.close()


async def _run_with_lock(playbook_id: UUID, schedule_id: UUID | None) -> dict[str, object]:
    lock_name = f"run:{playbook_id}:{schedule_id}" if schedule_id else f"run:{playbook_id}"
    lock_acquired = await acquire_lock_async(lock_name)
    if not lock_acquired:
        record_duplicate_skip()
        logger.info(
            "celery.hunt.skipped_duplicate",
            playbook_id=str(playbook_id),
            schedule_id=str(schedule_id) if schedule_id else None,
        )
        raise Ignore()

    try:
        return await _run_playbook(playbook_id, schedule_id)
    finally:
        await release_lock_async(lock_name)


def _run_async(playbook_id: UUID, schedule_id: UUID | None) -> dict[str, object]:
    return asyncio.run(_run_with_lock(playbook_id, schedule_id))


class RunPlaybookTask(Task):
    autoretry_for = (Exception,)
    retry_backoff = settings.task_retry_backoff_seconds
    retry_backoff_max = settings.task_retry_backoff_max_seconds
    retry_jitter = True
    retry_kwargs = {"max_retries": 5}

    def run(self, playbook_id: str, schedule_id: str | None = None) -> dict[str, object]:
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
        except Ignore:
            raise
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


run_playbook_task = celery_app.register_task(RunPlaybookTask())


def enqueue_run_playbook(
    playbook_id: str,
    schedule_id: str | None = None,
    *,
    source: str = "api",
) -> None:
    record_queue_enqueued(1, source)
    run_playbook_task.apply_async((playbook_id, schedule_id), ignore_result=True)


@worker_ready.connect
def _handle_worker_ready(sender, **kwargs) -> None:  # pragma: no cover - signal hook
    if sender.app is not celery_app:
        return
    logger.info("scheduler.reconcile.start")
    try:
        reconcile_schedules()
    except Exception:  # pragma: no cover - defensive logging
        logger.exception("scheduler.reconcile.failed")
