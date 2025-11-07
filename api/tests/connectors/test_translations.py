"""Translation tests for hunt connectors."""

from __future__ import annotations

from typing import Any

import pytest

from app.connectors.elastic import ElasticConnector
from app.connectors.sentinel import SentinelConnector
from app.connectors.splunk import SplunkConnector


@pytest.fixture
def sigma_rule() -> dict[str, Any]:
    return {
        "title": "Sample Rule",
        "detection": {
            "selection": {
                "EventID": 4625,
                "LogonType": [3, 10],
            }
        },
    }


@pytest.mark.parametrize(
    "connector_cls",
    [SplunkConnector, ElasticConnector, SentinelConnector],
)
def test_translate_generates_query(connector_cls, sigma_rule: dict[str, Any], monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SPLUNK_BASE_URL", "https://example.com")
    monkeypatch.setenv("SPLUNK_TOKEN", "token")
    monkeypatch.setenv("ELASTIC_URL", "https://elastic.local")
    monkeypatch.setenv("ELASTIC_USERNAME", "elastic")
    monkeypatch.setenv("ELASTIC_PASSWORD", "password")
    monkeypatch.setenv("SENTINEL_WORKSPACE_ID", "workspace")
    monkeypatch.setenv("SENTINEL_SHARED_KEY", "key")

    connector = connector_cls()  # type: ignore[call-arg]
    artifacts = connector.translate(sigma_rule)

    assert artifacts.translated_query == "EventID=4625 AND LogonType IN (3 OR 10)"
    assert artifacts.parameters["selection_fields"] == ["EventID", "LogonType"]
    assert artifacts.original_rule == sigma_rule


def test_splunk_connector_requires_configuration(monkeypatch: pytest.MonkeyPatch, sigma_rule: dict[str, Any]) -> None:
    monkeypatch.delenv("SPLUNK_BASE_URL", raising=False)
    monkeypatch.delenv("SPLUNK_TOKEN", raising=False)
    connector = SplunkConnector()
    assert connector.is_configured() is False
    with pytest.raises(RuntimeError):
        connector.execute(connector.translate(sigma_rule))
