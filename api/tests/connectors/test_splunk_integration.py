from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.connectors.base import QueryArtifacts
from app.connectors.splunk import SplunkConnector


SAMPLES_DIR = Path(__file__).resolve().parents[3] / "samples" / "logs"


class _FakeResponse:
    def __init__(self, rows: list[str]) -> None:
        self._rows = rows

    def raise_for_status(self) -> None:
        return None

    def iter_lines(self) -> list[str]:
        for row in self._rows:
            yield row


class _FakeClient:
    def __init__(self, rows: list[str]) -> None:
        self._response = _FakeResponse(rows)

    def post(self, *_: Any, **__: Any) -> _FakeResponse:
        return self._response


@pytest.mark.usefixtures("monkeypatch")
def test_splunk_execute_returns_records(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_path = SAMPLES_DIR / "saas_credential_stuffing.jsonl"
    assert sample_path.exists(), "Sample SaaS credential stuffing log missing"

    events = [json.loads(line) for line in sample_path.read_text().splitlines() if line]
    rows = [json.dumps({"result": event}) for event in events]

    connector = SplunkConnector()
    connector._client = _FakeClient(rows)  # type: ignore[attr-defined]

    artifacts = QueryArtifacts(original_rule={}, translated_query="search index=saas", parameters={})
    result = connector.execute(artifacts)

    assert len(result.records) == len(events)
    assert {record.payload["outcome"] for record in result.records} == {"failure", "success"}
    assert result.query is artifacts
