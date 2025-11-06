"""Shared pytest fixtures for API testing."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

# Configure test database before importing the FastAPI app so settings pick it up.
TEST_DB_PATH = Path(__file__).with_name("test.db")
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

os.environ.setdefault("DATABASE_URL", f"sqlite+aiosqlite:///{TEST_DB_PATH}")
os.environ.setdefault("INITIAL_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("INITIAL_ADMIN_PASSWORD", "ChangeMe123!")
os.environ.setdefault("ENABLE_METRICS", "false")

from app.main import app  # noqa: E402  (import after environment configuration)


@pytest.fixture(scope="session")
def api_client() -> Generator[TestClient, None, None]:
    """Provide a TestClient with application lifespan management."""

    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def admin_token(api_client: TestClient) -> str:
    """Return a bearer token for the seeded admin user."""

    response = api_client.post(
        "/api/auth/token",
        data={
            "username": os.environ["INITIAL_ADMIN_EMAIL"],
            "password": os.environ["INITIAL_ADMIN_PASSWORD"],
        },
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="session", autouse=True)
def cleanup_database() -> Generator[None, None, None]:
    """Remove the temporary SQLite database after tests run."""

    yield
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    journal = TEST_DB_PATH.with_suffix(TEST_DB_PATH.suffix + "-journal")
    if journal.exists():
        journal.unlink()
