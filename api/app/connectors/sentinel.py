"""Azure Sentinel (Log Analytics) connector implementation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.connectors.base import BaseConnector, ExecutionRecord, ExecutionResult, QueryArtifacts
from app.connectors.translator import translate_basic_selection
from app.core.config import Settings, get_settings

try:  # Optional dependency, only available with the `connectors` extra
    from azure.identity import ClientSecretCredential  # type: ignore
    from azure.monitor.query import LogsQueryClient  # type: ignore
    from azure.monitor.query import LogsQueryStatus  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    ClientSecretCredential = None  # type: ignore[misc]
    LogsQueryClient = None  # type: ignore[misc]
    LogsQueryStatus = None  # type: ignore[misc]


@dataclass(slots=True)
class SentinelAuth:
    tenant_id: str
    client_id: str
    client_secret: str


class SentinelConnector(BaseConnector):
    """Executes Sigma-derived hunts against Microsoft Sentinel."""

    def __init__(self, settings: Settings | None = None, *, timeout: float = 60.0) -> None:
        super().__init__(backend_id="sentinel")
        self.settings = settings or get_settings()
        self.timeout = timeout
        self._client = self._create_client()

    def _create_client(self) -> LogsQueryClient | None:  # type: ignore[override]
        if not self.is_configured() or ClientSecretCredential is None or LogsQueryClient is None:
            return None

        auth = SentinelAuth(
            tenant_id=self.settings.sentinel_tenant_id or "",
            client_id=self.settings.sentinel_client_id or "",
            client_secret=self.settings.sentinel_client_secret or "",
        )

        credential = ClientSecretCredential(
            tenant_id=auth.tenant_id,
            client_id=auth.client_id,
            client_secret=auth.client_secret,
        )
        return LogsQueryClient(credential, timeout=self.timeout)

    def is_configured(self) -> bool:
        return bool(
            self.settings.sentinel_workspace_id
            and self.settings.sentinel_tenant_id
            and self.settings.sentinel_client_id
            and self.settings.sentinel_client_secret
        )

    def translate(self, sigma_rule: dict[str, Any]) -> QueryArtifacts:
        return translate_basic_selection(sigma_rule, backend_name=self.backend_id)

    def execute(
        self,
        artifacts: QueryArtifacts,
        *,
        earliest: datetime | None = None,
        latest: datetime | None = None,
    ) -> ExecutionResult:
        if self._client is None or LogsQueryStatus is None:
            raise RuntimeError("Sentinel connector is not configured or dependency missing")

        query = artifacts.translated_query or "*\n| take 200"
        timespan = None
        if earliest or latest:
            timespan = (earliest or datetime.now(timezone.utc), latest or datetime.now(timezone.utc))

        start = datetime.now(timezone.utc)
        response = self._client.query_workspace(
            workspace_id=self.settings.sentinel_workspace_id,
            query=query,
            timespan=timespan,
        )

        records: list[ExecutionRecord] = []
        if response.status == LogsQueryStatus.SUCCESS:
            for table in response.tables or []:
                columns = [column.name for column in table.columns]
                for row in table.rows:
                    payload = {columns[idx]: value for idx, value in enumerate(row)}
                    timestamp_value = payload.get("TimeGenerated") or payload.get("timestamp")
                    timestamp = (
                        datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
                        if isinstance(timestamp_value, str)
                        else datetime.now(timezone.utc)
                    )
                    records.append(
                        ExecutionRecord(
                            timestamp=timestamp,
                            backend_id=self.backend_id,
                            payload=payload,
                            raw={"columns": columns, "row": row},
                        )
                    )
        else:
            message = getattr(response, "error", None)
            raise RuntimeError(f"Sentinel query failed: {message}")

        end = datetime.now(timezone.utc)
        return ExecutionResult(records=records, query=artifacts, started_at=start, finished_at=end)
