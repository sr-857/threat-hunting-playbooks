"""Application bootstrap helpers."""

from __future__ import annotations

from sqlalchemy import select

from app.core.config import get_settings
from app.db.base import Base
from app.db.schema_guard import ensure_schema_guard
from app.db.session import AsyncSessionLocal, engine
from app.models.playbook import Playbook
from app.services.user_store import ensure_initial_superuser

_default_playbooks = [
    {
        "name": "Suspicious PowerShell",
        "description": "Detects PowerShell executions using encoded commands.",
        "rule_path": "windows/suspicious_powershell.yml",
        "data_path": "logs/windows_process.jsonl",
        "data_format": "jsonl",
        "tags": ["windows", "powershell", "execution"],
    },
    {
        "name": "SaaS Credential Stuffing Campaign",
        "description": "Highlights distributed login failures followed by suspicious success and MFA bypass.",
        "rule_path": "saas/credential_stuffing.yml",
        "data_path": "logs/saas_credential_stuffing.jsonl",
        "data_format": "jsonl",
        "tags": ["saas", "identity", "credential-access"],
    },
    {
        "name": "SaaS OAuth Token Theft",
        "description": "Detects anomalous refresh token grants without MFA and downstream API abuse.",
        "rule_path": "saas/oauth_token_theft.yml",
        "data_path": "logs/saas_oauth_token_theft.jsonl",
        "data_format": "jsonl",
        "tags": ["saas", "identity", "persistence"],
    },
    {
        "name": "Linux SUID Dropper PrivEsc",
        "description": "Detects creation and execution of rogue SUID binaries for privilege escalation.",
        "rule_path": "linux/privilege_escalation_suid_dropper.yml",
        "data_path": "logs/linux_suid_dropper.jsonl",
        "data_format": "jsonl",
        "tags": ["linux", "privilege-escalation", "suid"],
    },
    {
        "name": "Sentinel Connector Abuse",
        "description": "Monitors bulk connector changes and automation disablement in Microsoft Sentinel.",
        "rule_path": "cloud/azure_sentinel_connector_abuse.yml",
        "data_path": "logs/azure_sentinel_connector_abuse.jsonl",
        "data_format": "jsonl",
        "tags": ["azure", "sentinel", "defense-evasion"],
    },
    {
        "name": "OT Network Reconnaissance",
        "description": "Flags ICS ladder logic enumeration and historian scraping attempts.",
        "rule_path": "ot/network_recon_ladder_logic.yml",
        "data_path": "logs/ot_network_recon.jsonl",
        "data_format": "jsonl",
        "tags": ["ot", "ics", "discovery"],
    },
]


async def init_db(seed: bool = True) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await ensure_schema_guard(engine)

    if not seed:
        return

    async with AsyncSessionLocal() as session:
        settings = get_settings()
        existing = await session.execute(select(Playbook.id).limit(1))
        if existing.first() is not None:
            await ensure_initial_superuser(
                session,
                email=settings.initial_admin_email,
                password=settings.initial_admin_password,
            )
            return

        for item in _default_playbooks:
            session.add(Playbook(**item))
        await ensure_initial_superuser(
            session,
            email=settings.initial_admin_email,
            password=settings.initial_admin_password,
        )
        await session.commit()
