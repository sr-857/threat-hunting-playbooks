"""Splunk connector implementation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import httpx

from app.connectors.base import BaseConnector, ExecutionRecord, ExecutionResult, QueryArtifacts
from app.connectors.translator import translate_basic_selection
from app.core.config import Settings, get_settings


class SplunkConnector(BaseConnector):
    """Executes Sigma-derived hunts against Splunk Enterprise / Cloud."""

    def __init__(self, settings: Settings | None = None, *, timeout: float = 60.0) -> None:
        super().__init__(backend_id="splunk")
        self.settings = settings or get_settings()
        self.timeout = timeout
        self._client: httpx.Client | None = self._create_client()

    def _create_client(self) -> httpx.Client | None:
        if not self.is_configured():
            return None

        base_url = self.settings.splunk_base_url
        assert base_url is not None

        headers = {}
        auth: httpx.Auth | None = None

        if self.settings.splunk_token:
            headers["Authorization"] = f"Splunk {self.settings.splunk_token}"
        elif self.settings.splunk_username and self.settings.splunk_password:
            auth = (self.settings.splunk_username, self.settings.splunk_password)
        else:  # This should not happen because is_configured() guards it.
            return None

        return httpx.Client(
            base_url=base_url.rstrip("/"),
            headers=headers,
            auth=auth,
            timeout=self.timeout,
            verify=self.settings.splunk_verify_ssl,
        )

    def is_configured(self) -> bool:
        return bool(
            self.settings.splunk_base_url
            and (
                self.settings.splunk_token
                or (self.settings.splunk_username and self.settings.splunk_password)
            )
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
        if self._client is None:
            raise RuntimeError("Splunk connector is not configured")

        search_query = artifacts.translated_query or "*"
        # Splunk requires searches to start with the `search` keyword unless it's a macro.
        if not search_query.lstrip().startswith("search"):
            search_query = f"search {search_query}"

        payload: dict[str, Any] = {
            "search": search_query,
            "output_mode": "json",
        }
        if earliest:
            payload["earliest_time"] = earliest.isoformat()
        if latest:
            payload["latest_time"] = latest.isoformat()

        start = datetime.now(timezone.utc)
        response = self._client.post("/services/search/jobs/export", data=payload)
        response.raise_for_status()

        records: list[ExecutionRecord] = []
        for line in response.iter_lines():
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            result = entry.get("result")
            if not isinstance(result, dict):
                continue
            timestamp_value = result.get("_time") or result.get("time")
            timestamp = (
                datetime.fromisoformat(timestamp_value.replace("Z", "+00:00"))
                if isinstance(timestamp_value, str)
                else datetime.now(timezone.utc)
            )
            records.append(
                ExecutionRecord(
                    timestamp=timestamp,
                    backend_id=self.backend_id,
                    payload=result,
                    raw=entry,
                )
            )

        end = datetime.now(timezone.utc)
        return ExecutionResult(records=records, query=artifacts, started_at=start, finished_at=end)
