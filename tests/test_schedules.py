"""Tests for schedule listing and role-based access."""

from __future__ import annotations

from fastapi.testclient import TestClient

from .conftest import admin_token, api_client


def test_schedule_list_requires_auth(api_client: TestClient) -> None:
    response = api_client.get("/api/schedules/")
    assert response.status_code == 401


def test_schedule_list_authorized(api_client: TestClient, admin_token: str) -> None:
    response = api_client.get(
        "/api/schedules/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
