"""Schedule management routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session_dependency
from app.schemas.schedule import HuntScheduleCreate, HuntScheduleRead, HuntScheduleUpdate
from app.scheduler.tasks import run_playbook_task
from app.services.playbook_store import PlaybookNotFoundError, get_playbook
from app.services.schedule_store import (
    HuntScheduleNotFoundError,
    create_schedule,
    delete_schedule,
    get_schedule,
    list_schedules,
    update_schedule,
)

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("/", response_model=list[HuntScheduleRead])
async def list_schedules_endpoint(
    session: AsyncSession = Depends(get_session_dependency()),
) -> list[HuntScheduleRead]:
    return await list_schedules(session)


@router.post("/", response_model=HuntScheduleRead, status_code=status.HTTP_201_CREATED)
async def create_schedule_endpoint(
    data: HuntScheduleCreate,
    session: AsyncSession = Depends(get_session_dependency()),
) -> HuntScheduleRead:
    try:
        await get_playbook(session, data.playbook_id)
    except PlaybookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return await create_schedule(session, data)


@router.get("/{schedule_id}", response_model=HuntScheduleRead)
async def get_schedule_endpoint(
    schedule_id: UUID,
    session: AsyncSession = Depends(get_session_dependency()),
) -> HuntScheduleRead:
    try:
        return await get_schedule(session, schedule_id)
    except HuntScheduleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.put("/{schedule_id}", response_model=HuntScheduleRead)
async def update_schedule_endpoint(
    schedule_id: UUID,
    data: HuntScheduleUpdate,
    session: AsyncSession = Depends(get_session_dependency()),
) -> HuntScheduleRead:
    try:
        return await update_schedule(session, schedule_id, data)
    except HuntScheduleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule_endpoint(
    schedule_id: UUID,
    session: AsyncSession = Depends(get_session_dependency()),
) -> None:
    try:
        await delete_schedule(session, schedule_id)
    except HuntScheduleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{schedule_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def run_schedule_endpoint(
    schedule_id: UUID,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_session_dependency()),
) -> dict[str, str]:
    try:
        schedule = await get_schedule(session, schedule_id)
    except HuntScheduleNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    background_tasks.add_task(
        run_playbook_task.delay,
        str(schedule.playbook_id),
        str(schedule.id),
    )

    return {"status": "scheduled"}
