from __future__ import annotations

from datetime import datetime
from typing import Any

import pytest

from app.connectors.base import ExecutionRecord, QueryArtifacts
from app.connectors import sentinel as sentinel_module
from app.connectors.sentinel import SentinelConnector


class _FakeLogsQueryClient:
    def __init__(self, tables: list[Any]) -> None:
        self._tables = tables

    def query_workspace(self, *args: Any, **kwargs: Any) -> Any:  # noqa: D401 - mimic SDK
        return type(
            "FakeResponse",
            (),
            {
                "status": sentinel_module.LogsQueryStatus.SUCCESS,  # type: ignore[attr-defined]
                "tables": self._tables,
            },
        )()


class _FakeTable:
    def __init__(self, columns: list[str], rows: list[list[Any]]) -> None:
        self.columns = [type("FakeColumn", (), {"name": name}) for name in columns]
        self.rows = rows


@pytest.mark.usefixtures("monkeypatch")
def test_sentinel_execute_returns_records(monkeypatch: pytest.MonkeyPatch) -> None:
    # Ensure configuration passes is_configured checks
    monkeypatch.setenv("SENTINEL_WORKSPACE_ID", "workspace")
    monkeypatch.setenv("SENTINEL_TENANT_ID", "tenant")
    monkeypatch.setenv("SENTINEL_CLIENT_ID", "client")
    monkeypatch.setenv("SENTINEL_CLIENT_SECRET", "secret")

    # Monkeypatch missing Azure dependencies with lightweight stand-ins
    sentinel_module.LogsQueryStatus = type("Status", (), {"SUCCESS": object()})  # type: ignore[attr-defined]

    table = _FakeTable(
        columns=["TimeGenerated", "OperationName", "Properties"],
        rows=[
            [
                "2025-08-02T12:00:00Z",
                "MICROSOFT.SECURITYINSIGHTS/DATACONNECTORS/WRITE",
                {"ingestionStatus": "Disabled"},
            ]
        ],
    )

    connector = SentinelConnector()
    connector._client = _FakeLogsQueryClient([table])  # type: ignore[attr-defined]

    artifacts = QueryArtifacts(original_rule={}, translated_query="datatable(...)", parameters={})
    result = connector.execute(artifacts)

    assert len(result.records) == 1
    record = result.records[0]
    assert isinstance(record, ExecutionRecord)
    assert record.payload["OperationName"].endswith("DATACONNECTORS/WRITE")
    assert isinstance(record.timestamp, datetime)
    assert result.query is artifacts
