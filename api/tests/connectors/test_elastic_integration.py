from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from app.connectors.base import QueryArtifacts
from app.connectors.elastic import ElasticConnector


SAMPLES_DIR = Path(__file__).resolve().parents[3] / "samples" / "logs"


class _FakeElasticClient:
    def __init__(self, hits: list[dict[str, Any]]) -> None:
        self._hits = hits

    def search(self, *args: Any, **kwargs: Any) -> dict[str, Any]:  # noqa: D401 - mimic elastic client
        return {"hits": {"hits": self._hits}}


@pytest.mark.usefixtures("monkeypatch")
def test_elastic_execute_returns_records(monkeypatch: pytest.MonkeyPatch) -> None:
    sample_path = SAMPLES_DIR / "linux_suid_dropper.jsonl"
    assert sample_path.exists(), "Sample Linux SUID dropper log missing"

    events = [json.loads(line) for line in sample_path.read_text().splitlines() if line]
    hits = [{"_source": event} for event in events]

    connector = ElasticConnector()
    connector._client = _FakeElasticClient(hits)  # type: ignore[attr-defined]

    artifacts = QueryArtifacts(original_rule={}, translated_query="process.executable:kworker", parameters={})
    result = connector.execute(artifacts)

    assert len(result.records) == len(events)
    assert {record.payload.get("process") for record in result.records if record.payload}  # basic smoke check
    assert result.query is artifacts
