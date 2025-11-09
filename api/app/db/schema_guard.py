"""Lightweight Alembic-style safeguards for database indexes and version gating."""

from __future__ import annotations

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

EXPECTED_SCHEMA_REVISION = "20241109_gating_indexes"

logger = structlog.get_logger(__name__)


async def ensure_schema_guard(engine: AsyncEngine) -> None:
    """Ensure the database has required indexes and expected schema revision."""

    async with engine.begin() as conn:
        await _ensure_version_table(conn)
        current = await _get_current_revision(conn)

        if current is None:
            logger.info("schema_guard.initialize", revision=EXPECTED_SCHEMA_REVISION)
            await _apply_required_indexes(conn)
            await _set_revision(conn, EXPECTED_SCHEMA_REVISION)
            return

        if current != EXPECTED_SCHEMA_REVISION:
            logger.error(
                "schema_guard.revision_mismatch",
                expected=EXPECTED_SCHEMA_REVISION,
                actual=current,
            )
            raise RuntimeError(
                "Database schema revision is out of date. "
                "Run migrations before starting the API."
            )

        # Revision matches the expected value; make sure safety indexes exist.
        await _apply_required_indexes(conn)


async def _ensure_version_table(conn: AsyncConnection) -> None:
    await conn.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(255) PRIMARY KEY
            )
            """
        )
    )


async def _get_current_revision(conn: AsyncConnection) -> str | None:
    result = await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
    row = result.first()
    return row[0] if row else None


async def _set_revision(conn: AsyncConnection, revision: str) -> None:
    await conn.execute(text("DELETE FROM alembic_version"))
    await conn.execute(
        text("INSERT INTO alembic_version (version_num) VALUES (:revision)"),
        {"revision": revision},
    )


async def _apply_required_indexes(conn: AsyncConnection) -> None:
    statements = [
        """
        CREATE INDEX IF NOT EXISTS ix_hunt_schedules_enabled_next_run_at
        ON hunt_schedules (enabled, next_run_at)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_hunt_schedules_playbook_id
        ON hunt_schedules (playbook_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS ix_playbooks_enabled
        ON playbooks (enabled)
        """,
    ]

    for stmt in statements:
        await conn.execute(text(stmt))
