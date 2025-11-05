"""Base classes and data structures for hunt connectors."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Iterable


@dataclass(slots=True)
class QueryArtifacts:
    """Artifacts generated when translating a Sigma rule for a backend."""

    original_rule: dict[str, Any]
    translated_query: str
    parameters: dict[str, Any]


@dataclass(slots=True)
class ExecutionRecord:
    """A single record returned by a hunt execution."""

    timestamp: datetime
    backend_id: str
    payload: dict[str, Any]
    raw: dict[str, Any] | None = None


@dataclass(slots=True)
class ExecutionResult:
    """Container summarising execution output."""

    records: list[ExecutionRecord]
    query: QueryArtifacts
    started_at: datetime
    finished_at: datetime

    @property
    def duration(self) -> timedelta:
        return self.finished_at - self.started_at


class BaseConnector(ABC):
    """Interface implemented by all hunt execution connectors."""

    backend_id: str

    def __init__(self, backend_id: str) -> None:
        self.backend_id = backend_id

    @abstractmethod
    def translate(self, sigma_rule: dict[str, Any]) -> QueryArtifacts:
        """Translate a Sigma rule into backend-specific artifacts."""

    @abstractmethod
    def execute(self, artifacts: QueryArtifacts, *, earliest: datetime | None = None, latest: datetime | None = None) -> ExecutionResult:
        """Execute the translated query and return records."""

    @abstractmethod
    def is_configured(self) -> bool:
        """Return True if the connector has sufficient configuration to run."""


def build_filter_from_selection(selection: dict[str, Any]) -> str:
    """Fallback query builder translating Sigma selection maps into simple predicates."""

    clauses: list[str] = []
    for field, expected in selection.items():
        if isinstance(expected, list):
            value = " OR ".join(str(item) for item in expected)
            clauses.append(f"{field} IN ({value})")
        else:
            clauses.append(f"{field}={expected}")
    return " AND ".join(clauses)
