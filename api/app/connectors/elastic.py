"""Elasticsearch connector for executing Sigma-derived hunts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.connectors.base import BaseConnector, ExecutionRecord, ExecutionResult, QueryArtifacts
from app.connectors.translator import translate_basic_selection
from app.core.config import Settings, get_settings

try:  # Optional dependency; only available when `connectors` extra is installed
    from elasticsearch import Elasticsearch  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    Elasticsearch = None  # type: ignore[misc]


class ElasticConnector(BaseConnector):
    """Executes hunts against Elasticsearch clusters."""

    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__(backend_id="elastic")
        self.settings = settings or get_settings()
        self._client = self._create_client()

    def _create_client(self) -> Elasticsearch | None:  # type: ignore[override]
        if not self.is_configured() or Elasticsearch is None:
            return None

        if self.settings.elastic_cloud_id:
            return Elasticsearch(
                cloud_id=self.settings.elastic_cloud_id,
                api_key=self.settings.elastic_api_key,
            )

        endpoint = self.settings.elastic_endpoint
        if not endpoint:
            return None

        if self.settings.elastic_api_key:
            return Elasticsearch(endpoint, api_key=self.settings.elastic_api_key)

        if self.settings.elastic_username and self.settings.elastic_password:
            return Elasticsearch(
                endpoint,
                basic_auth=(self.settings.elastic_username, self.settings.elastic_password),
            )

        return Elasticsearch(endpoint)

    def is_configured(self) -> bool:
        return bool(
            (self.settings.elastic_endpoint or self.settings.elastic_cloud_id)
            and (self.settings.elastic_api_key or self.settings.elastic_username)
        ) or bool(self.settings.elastic_cloud_id and self.settings.elastic_api_key)

    def translate(self, sigma_rule: dict[str, Any]) -> QueryArtifacts:
        return translate_basic_selection(sigma_rule, backend_name=self.backend_id)

    def execute(
        self,
        artifacts: QueryArtifacts,
        *,
        earliest: datetime | None = None,
        latest: datetime | None = None,
    ) -> ExecutionResult:
        if self._client is None:
            raise RuntimeError("Elasticsearch connector is not configured or dependency missing")

        start = datetime.now(timezone.utc)

        query_string = artifacts.translated_query or "*"
        must_clauses: list[dict[str, Any]] = [{"query_string": {"query": query_string}}]
        filter_clauses: list[dict[str, Any]] = []

        if earliest or latest:
            range_filter: dict[str, Any] = {"@timestamp": {}}
            if earliest:
                range_filter["@timestamp"]["gte"] = earliest.isoformat()
            if latest:
                range_filter["@timestamp"]["lte"] = latest.isoformat()
            filter_clauses.append({"range": range_filter})

        body_query: dict[str, Any] = {"bool": {"must": must_clauses}}
        if filter_clauses:
            body_query["bool"]["filter"] = filter_clauses

        response = self._client.search(  # type: ignore[call-arg]
            index="*",
            query=body_query,
            size=200,
        )

        hits = response.get("hits", {}).get("hits", [])
        records: list[ExecutionRecord] = []
        for hit in hits:
            source = hit.get("_source", {})
            timestamp_value = source.get("@timestamp") or hit.get("_source", {}).get("timestamp")
            timestamp = (
                datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
                if isinstance(timestamp_value, str)
                else datetime.now(timezone.utc)
            )
            records.append(
                ExecutionRecord(
                    timestamp=timestamp,
                    backend_id=self.backend_id,
                    payload=source,
                    raw=hit,
                )
            )

        end = datetime.now(timezone.utc)
        return ExecutionResult(records=records, query=artifacts, started_at=start, finished_at=end)
