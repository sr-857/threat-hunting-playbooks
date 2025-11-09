"""Utilities for working with Sigma rules and local datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

import yaml


def load_sigma_rules(rule_path: Path) -> list[dict[str, Any]]:
    """Load a Sigma rule file from disk."""
    with rule_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return [data]
    raise ValueError(f"Unsupported Sigma file format at {rule_path}")


def iter_jsonl_records(data_path: Path) -> Iterable[dict[str, Any]]:
    """Yield JSON records from a newline-delimited file."""
    with data_path.open("r", encoding="utf-8") as data_file:
        for line in data_file:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def match_value(value: Any, expected: Any, modifier: str | None) -> bool:
    """Perform basic Sigma comparison operations."""
    if isinstance(value, str) and isinstance(expected, str):
        value_lower = value.lower()
        expected_lower = expected.lower()
        if modifier == "contains":
            return expected_lower in value_lower
        if modifier == "startswith":
            return value_lower.startswith(expected_lower)
        if modifier == "endswith":
            return value_lower.endswith(expected_lower)
        return value_lower == expected_lower
    if isinstance(expected, list):
        return any(match_value(value, item, modifier) for item in expected)
    return value == expected


def record_matches_selection(record: dict[str, Any], selection: dict[str, Any]) -> bool:
    """Evaluate whether a record satisfies a Sigma selection map."""
    for field, expected in selection.items():
        base_field, modifier = field.split("|", maxsplit=1) if "|" in field else (field, None)
        if base_field not in record:
            return False
        if not match_value(record[base_field], expected, modifier):
            return False
    return True


class SigmaValidationError(ValueError):
    """Raised when a Sigma rule fails validation."""


def validate_sigma_rules(rules: list[dict[str, Any]]) -> None:
    """Ensure incoming Sigma rules contain required metadata and detection clauses."""

    if not rules:
        raise SigmaValidationError("No Sigma rules were provided")

    for index, rule in enumerate(rules):
        context = rule.get("title") or f"rule[{index}]"

        if not isinstance(rule, dict):
            raise SigmaValidationError(f"{context}: rule must be a mapping")

        title = rule.get("title")
        if not isinstance(title, str) or not title.strip():
            raise SigmaValidationError(f"{context}: missing or empty 'title'")

        logsource = rule.get("logsource")
        if not isinstance(logsource, dict) or not logsource:
            raise SigmaValidationError(f"{context}: missing 'logsource' definition")

        detection = rule.get("detection")
        if not isinstance(detection, dict):
            raise SigmaValidationError(f"{context}: missing 'detection' section")

        selection = detection.get("selection")
        if not isinstance(selection, dict) or not selection:
            raise SigmaValidationError(f"{context}: detection.selection must be a non-empty mapping")

        for field, value in selection.items():
            if value in (None, ""):
                raise SigmaValidationError(
                    f"{context}: detection selection '{field}' cannot be empty"
                )

