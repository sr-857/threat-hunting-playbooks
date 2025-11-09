"""Helpers for translating Sigma rules into backend-specific artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.connectors.base import QueryArtifacts, build_filter_from_selection
from app.utils.sigma import SigmaValidationError, validate_sigma_rules


@dataclass(slots=True)
class TranslationContext:
    """Context passed to translation helpers."""

    backend_name: str
    default_index: str | None = None


def translate_basic_selection(rule: dict[str, Any], backend_name: str) -> QueryArtifacts:
    """Translate a simple Sigma rule selection into a string query.

    This is a lightweight fallback used until full backend-specific translators
    are implemented. It inspects the first selection block and renders a generic
    predicate expression that downstream connectors can adapt as needed.
    """

    validate_sigma_rules([rule])

    detection = rule.get("detection", {})
    selection = detection.get("selection", {})
    translated_query = build_filter_from_selection(selection) if selection else "*"
    parameters = {
        "backend": backend_name,
        "selection_fields": list(selection.keys()),
    }
    return QueryArtifacts(original_rule=rule, translated_query=translated_query, parameters=parameters)
