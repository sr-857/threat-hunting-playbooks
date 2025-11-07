"""Shared pytest fixtures for API testing."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Generator
import json
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DB_PATH = Path(__file__).with_name("test.db")
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

PREVIOUS_DATABASE_URL = os.environ.get("DATABASE_URL")
TEST_DATABASE_URL = f"sqlite+aiosqlite:///{TEST_DB_PATH}"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("INITIAL_ADMIN_EMAIL", "admin@example.com")
os.environ.setdefault("INITIAL_ADMIN_PASSWORD", "ChangeMe123!")
os.environ.setdefault("ENABLE_METRICS", "false")

FIXTURE_ROOT = Path(__file__).resolve().parent
DATA_ROOT = FIXTURE_ROOT / "_data"
RULES_ROOT = DATA_ROOT / "rules"
SAMPLES_ROOT = DATA_ROOT / "samples"
ARTIFACTS_ROOT = DATA_ROOT / "artifacts"

RULES_ROOT.joinpath("windows").mkdir(parents=True, exist_ok=True)
SAMPLES_ROOT.joinpath("logs").mkdir(parents=True, exist_ok=True)
ARTIFACTS_ROOT.mkdir(parents=True, exist_ok=True)

RULE_FILE = RULES_ROOT / "windows" / "suspicious_powershell.yml"
if not RULE_FILE.exists():
    RULE_FILE.write_text(
        """title: Suspicious PowerShell\ndescription: Test rule\nlogsource:\n  product: windows\ndetection:\n  selection:\n    EventID: 4104\ncondition: selection\n""",
        encoding="utf-8",
    )

SAMPLE_FILE = SAMPLES_ROOT / "logs" / "windows_process.jsonl"
if not SAMPLE_FILE.exists():
    SAMPLE_FILE.write_text(json.dumps({"EventID": 4104}) + "\n", encoding="utf-8")

os.environ.setdefault("SAMPLES_ROOT", str(SAMPLES_ROOT))
os.environ.setdefault("RULES_ROOT", str(RULES_ROOT))
os.environ.setdefault("ARTIFACTS_ROOT", str(ARTIFACTS_ROOT))

BASE_DIR = Path(__file__).resolve().parents[1]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.core import config as app_config  # noqa: E402

app_config.get_settings.cache_clear()
test_settings = app_config.get_settings()

from app.db import session as db_session  # noqa: E402

sqlite_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
try:
    db_session.engine.sync_engine.dispose()
except AttributeError:
    pass
db_session.engine = sqlite_engine
db_session.AsyncSessionLocal = async_sessionmaker(sqlite_engine, expire_on_commit=False, class_=AsyncSession)
db_session.settings = test_settings

from app.services import bootstrap as bootstrap_services  # noqa: E402
from app.api import deps as api_deps  # noqa: E402

try:
    from app.scheduler import tasks as scheduler_tasks  # noqa: E402
except Exception:  # pragma: no cover - scheduler optional in tests
    scheduler_tasks = None

bootstrap_services.engine = db_session.engine
bootstrap_services.AsyncSessionLocal = db_session.AsyncSessionLocal
api_deps.AsyncSessionLocal = db_session.AsyncSessionLocal
if scheduler_tasks is not None:
    scheduler_tasks.AsyncSessionLocal = db_session.AsyncSessionLocal

import app.main as app_main  # noqa: E402

app_main.settings = test_settings

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

    if PREVIOUS_DATABASE_URL is not None:
        os.environ["DATABASE_URL"] = PREVIOUS_DATABASE_URL
    else:
        os.environ.pop("DATABASE_URL", None)
