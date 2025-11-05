"""Telemetry endpoints for hunt monitoring."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.telemetry import list_hunt_alerts, list_hunt_events

router = APIRouter(prefix="/telemetry", tags=["telemetry"])


@router.get("/events")
def get_hunt_events(limit: int = Query(50, ge=1, le=500)) -> list[dict[str, object]]:
    """Return recent hunt execution events."""

    return list_hunt_events(limit)


@router.get("/alerts")
def get_hunt_alerts(limit: int = Query(50, ge=1, le=500)) -> list[dict[str, object]]:
    """Return recent hunt alerts above the confidence threshold."""

    return list_hunt_alerts(limit)
