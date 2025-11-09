from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest

from app.connectors.translator import translate_basic_selection
from app.schemas.playbook import PlaybookRead
from app.services.playbook_store import execute_playbook_local
from app.utils.sigma import SigmaValidationError

from .conftest import RULES_ROOT, SAMPLES_ROOT


def _write_file(path: Path, contents: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def test_execute_playbook_local_rejects_invalid_rule() -> None:
    rule_path = RULES_ROOT / "invalid" / "missing_detection.yml"
    sample_path = SAMPLES_ROOT / "logs" / "invalid.jsonl"

    _write_file(
        rule_path,
        """title: Invalid Rule Missing Detection
logsource:
  product: test
""",
    )
    _write_file(sample_path, "{}\n")

    playbook = PlaybookRead(
        id=uuid4(),
        name="Invalid Rule Playbook",
        description=None,
        rule_path=str(rule_path.relative_to(RULES_ROOT)),
        data_path=str(sample_path.relative_to(SAMPLES_ROOT.parent)),
        data_format="jsonl",
        tags=[],
        enabled=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    with pytest.raises(ValueError) as excinfo:
        execute_playbook_local(playbook)
    assert "Invalid Sigma rule file" in str(excinfo.value)


def test_translate_basic_selection_rejects_invalid_rule() -> None:
    invalid_rule: dict[str, object] = {"title": "Rule Without Detection"}

    with pytest.raises(SigmaValidationError):
        translate_basic_selection(invalid_rule, backend_name="splunk")
