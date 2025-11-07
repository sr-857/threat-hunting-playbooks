"""Authentication happy-path and protection checks."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_token_allows_access_to_playbooks(api_client: TestClient, admin_token: str) -> None:
    response = api_client.get(
        "/api/playbooks/",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert isinstance(payload, list)


def test_playbook_run_requires_valid_token(api_client: TestClient, admin_token: str) -> None:
    playbooks = api_client.get(
        "/api/playbooks/",
        headers={"Authorization": f"Bearer {admin_token}"},
    ).json()
    assert playbooks, "Expected seeded playbooks to be available"

    playbook_id = playbooks[0]["id"]

    unauthenticated = api_client.post(f"/api/playbooks/{playbook_id}/run")
    assert unauthenticated.status_code == 401

    authorized = api_client.post(
        f"/api/playbooks/{playbook_id}/run",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert authorized.status_code == 200, authorized.text
    data = authorized.json()
    assert data["playbook"]["id"] == playbook_id
