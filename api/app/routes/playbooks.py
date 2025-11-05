"""Playbook API routes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session_dependency
from app.schemas.playbook import PlaybookRead, PlaybookRunResponse
from app.services.playbook_store import (
    PlaybookNotFoundError,
    execute_playbook_local,
    get_playbook,
    list_playbooks,
)

router = APIRouter(prefix="/playbooks", tags=["playbooks"])


@router.get("/", response_model=list[PlaybookRead])
async def list_playbook_endpoint(
    session: AsyncSession = Depends(get_session_dependency()),
) -> list[PlaybookRead]:
    return await list_playbooks(session)


@router.get("/{playbook_id}", response_model=PlaybookRead)
async def get_playbook_endpoint(
    playbook_id: UUID,
    session: AsyncSession = Depends(get_session_dependency()),
) -> PlaybookRead:
    try:
        return await get_playbook(session, playbook_id)
    except PlaybookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{playbook_id}/run", response_model=PlaybookRunResponse)
async def run_playbook_endpoint(
    playbook_id: UUID,
    session: AsyncSession = Depends(get_session_dependency()),
) -> PlaybookRunResponse:
    try:
        playbook = await get_playbook(session, playbook_id)
    except PlaybookNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    result = execute_playbook_local(playbook)
    return PlaybookRunResponse(playbook=playbook, result=result)
