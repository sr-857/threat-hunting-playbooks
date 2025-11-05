"""Application bootstrap helpers."""

from __future__ import annotations

from sqlalchemy import select

from app.db.base import Base
from app.db.session import AsyncSessionLocal, engine
from app.models.playbook import Playbook

_default_playbooks = [
    {
        "name": "Suspicious PowerShell",
        "description": "Detects PowerShell executions using encoded commands.",
        "rule_path": "windows/suspicious_powershell.yml",
        "data_path": "logs/windows_process.jsonl",
        "data_format": "jsonl",
        "tags": ["windows", "powershell", "execution"],
    }
]


async def init_db(seed: bool = True) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    if not seed:
        return

    async with AsyncSessionLocal() as session:
        existing = await session.execute(select(Playbook.id).limit(1))
        if existing.first() is not None:
            return

        for item in _default_playbooks:
            session.add(Playbook(**item))
        await session.commit()
