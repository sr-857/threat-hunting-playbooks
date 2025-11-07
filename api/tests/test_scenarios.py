"""Scenario-focused integration tests covering end-to-end hunt execution."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from .conftest import ARTIFACTS_ROOT, RULES_ROOT, SAMPLES_ROOT, admin_token, api_client


def _write_rule(relative_path: str, contents: str) -> Path:
    rule_path = RULES_ROOT.joinpath(relative_path)
    rule_path.parent.mkdir(parents=True, exist_ok=True)
    if not rule_path.exists():
        rule_path.write_text(contents, encoding="utf-8")
    return rule_path


def _write_sample(relative_path: str, records: list[dict[str, object]]) -> Path:
    sample_path = SAMPLES_ROOT.joinpath(relative_path)
    sample_path.parent.mkdir(parents=True, exist_ok=True)
    if not sample_path.exists():
        sample_payload = "\n".join(json.dumps(record) for record in records) + "\n"
        sample_path.write_text(sample_payload, encoding="utf-8")
    return sample_path


def _ensure_saas_assets() -> None:
    """Write minimal Sigma rule and sample data for SaaS credential stuffing scenario."""

    _write_rule(
        "saas/credential_stuffing.yml",
        """title: SaaS Credential Stuffing Demo
id: 99999999-aaaa-bbbb-cccc-eeeeeeeeeeee
description: Minimal rule for scenario-based testing.
status: experimental
logsource:
  category: authentication
detection:
  selection:
    outcome: success
  condition: selection
falsepositives:
  - Legitimate admin testing
level: high
""",
    )

    _write_sample(
        "logs/saas_credential_stuffing.jsonl",
        [
            {
                "username": "victim@example.com",
                "ip_address": "198.51.100.23",
                "outcome": "success",
                "notes": "Test record for scenario validation",
            }
        ],
    )


def _ensure_linux_assets() -> None:
    """Write minimal Sigma rule and sample data for Linux SUID dropper scenario."""

    _write_rule(
        "linux/privilege_escalation_suid_dropper.yml",
        """title: Linux SUID Dropper Demo
id: 77777777-aaaa-bbbb-cccc-ffffffffffff
description: Minimal rule for Linux privilege escalation scenario testing.
status: experimental
logsource:
  product: linux
detection:
  selection:
    action: chmod
  condition: selection
falsepositives:
  - Legitimate configuration management
level: high
""",
    )

    _write_sample(
        "logs/linux_suid_dropper.jsonl",
        [
            {
                "host": "demo-linux",
                "action": "chmod",
                "path": "/tmp/.cache/suid-helper",
                "user": "attacker",
            }
        ],
    )


def _ensure_oauth_assets() -> None:
    """Write minimal Sigma rule and sample data for SaaS OAuth token theft scenario."""

    _write_rule(
        "saas/oauth_token_theft.yml",
        """title: SaaS OAuth Token Theft Demo
id: 88888888-aaaa-bbbb-cccc-ffffffffffff
description: Minimal rule for SaaS OAuth token theft scenario testing.
status: experimental
logsource:
  category: authentication
detection:
  selection:
    grant_type: refresh_token
    mfa_bypass: true
  condition: selection
falsepositives:
  - Legitimate administrator token refresh
level: high
""",
    )

    _write_sample(
        "logs/saas_oauth_token_theft.jsonl",
        [
            {
                "user": "victim@example.com",
                "grant_type": "refresh_token",
                "mfa_bypass": True,
                "ip_address": "203.0.113.55",
            }
        ],
    )


def _ensure_sentinel_assets() -> None:
    """Write minimal Sigma rule and sample data for Sentinel connector abuse scenario."""

    _write_rule(
        "cloud/azure_sentinel_connector_abuse.yml",
        """title: Sentinel Connector Abuse Demo
id: 66666666-aaaa-bbbb-cccc-ffffffffffff
description: Minimal rule for Sentinel connector abuse scenario testing.
status: experimental
logsource:
  product: azure
detection:
  selection:
    operationName: DisableAutomationRule
  condition: selection
falsepositives:
  - Planned maintenance window
level: high
""",
    )

    _write_sample(
        "logs/azure_sentinel_connector_abuse.jsonl",
        [
            {
                "workspace": "demo-workspace",
                "operationName": "DisableAutomationRule",
                "operator": "attacker@contoso.com",
            }
        ],
    )


def _ensure_ot_assets() -> None:
    """Write minimal Sigma rule and sample data for OT network reconnaissance scenario."""

    _write_rule(
        "ot/network_recon_ladder_logic.yml",
        """title: OT Network Recon Demo
id: 55555555-aaaa-bbbb-cccc-ffffffffffff
description: Minimal rule for OT network reconnaissance scenario testing.
status: experimental
logsource:
  product: ics
detection:
  selection:
    protocol: s7comm
  condition: selection
falsepositives:
  - Legitimate engineering workstation testing
level: high
""",
    )

    _write_sample(
        "logs/ot_network_recon.jsonl",
        [
            {
                "asset": "plc-1",
                "protocol": "s7comm",
                "source_ip": "10.20.30.40",
            }
        ],
    )


def _run_playbook(
    client: TestClient,
    token: str,
    playbook_name: str,
    *,
    expected_matches: int = 1,
    expected_total: int = 1,
) -> tuple[dict[str, object], dict[str, object]]:
    headers = {"Authorization": f"Bearer {token}"}
    playbooks_response = client.get("/api/playbooks/", headers=headers)
    assert playbooks_response.status_code == 200, playbooks_response.text

    playbooks = playbooks_response.json()
    target = next((item for item in playbooks if item["name"] == playbook_name), None)
    assert target, f"Expected {playbook_name!r} to be seeded"

    run_response = client.post(
        f"/api/playbooks/{target['id']}/run",
        headers=headers,
    )
    assert run_response.status_code == 200, run_response.text

    payload = run_response.json()
    result = payload["result"]

    assert result["matched_count"] == expected_matches
    assert result["total_records"] == expected_total
    assert result["confidence"] == (
        expected_matches / expected_total if expected_total else 0.0
    )

    return payload, target


def test_saas_credential_stuffing_end_to_end(api_client: TestClient, admin_token: str) -> None:
    """Run the seeded SaaS credential stuffing playbook and validate outputs."""

    _ensure_saas_assets()

    payload, target = _run_playbook(
        api_client,
        admin_token,
        "SaaS Credential Stuffing Campaign",
    )

    result = payload["result"]
    assert result["execution_notes"] == "Local execution against JSONL sample data"

    telemetry = payload.get("telemetry")
    assert telemetry is not None
    assert telemetry["playbook_id"] == target["id"]
    assert telemetry["matched_count"] == 1

    artifact_path = Path(result["artifact_paths"]["result"])
    assert artifact_path.exists(), f"Artifact file missing: {artifact_path}"

    artifact_data = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert artifact_data["matched_count"] == 1
    assert artifact_data["confidence"] == 1.0

    # Ensure artifact lives under the configured artifacts root
    assert ARTIFACTS_ROOT in artifact_path.parents


def test_linux_suid_dropper_end_to_end(api_client: TestClient, admin_token: str) -> None:
    """Run the seeded Linux SUID dropper playbook and validate outputs."""

    _ensure_linux_assets()

    payload, _ = _run_playbook(
        api_client,
        admin_token,
        "Linux SUID Dropper PrivEsc",
    )

    artifact_path = Path(payload["result"]["artifact_paths"]["result"])
    assert artifact_path.exists(), f"Artifact file missing: {artifact_path}"
    assert ARTIFACTS_ROOT in artifact_path.parents


def test_saas_oauth_token_theft_end_to_end(api_client: TestClient, admin_token: str) -> None:
    """Run the seeded SaaS OAuth token theft playbook and validate outputs."""

    _ensure_oauth_assets()

    payload, _ = _run_playbook(
        api_client,
        admin_token,
        "SaaS OAuth Token Theft",
    )

    artifact_path = Path(payload["result"]["artifact_paths"]["result"])
    assert artifact_path.exists(), f"Artifact file missing: {artifact_path}"
    assert ARTIFACTS_ROOT in artifact_path.parents


def test_sentinel_connector_abuse_end_to_end(api_client: TestClient, admin_token: str) -> None:
    """Run the seeded Sentinel connector abuse playbook and validate outputs."""

    _ensure_sentinel_assets()

    payload, _ = _run_playbook(
        api_client,
        admin_token,
        "Sentinel Connector Abuse",
    )

    artifact_path = Path(payload["result"]["artifact_paths"]["result"])
    assert artifact_path.exists(), f"Artifact file missing: {artifact_path}"
    assert ARTIFACTS_ROOT in artifact_path.parents


def test_ot_network_recon_end_to_end(api_client: TestClient, admin_token: str) -> None:
    """Run the seeded OT network reconnaissance playbook and validate outputs."""

    _ensure_ot_assets()

    payload, _ = _run_playbook(
        api_client,
        admin_token,
        "OT Network Reconnaissance",
    )

    artifact_path = Path(payload["result"]["artifact_paths"]["result"])
    assert artifact_path.exists(), f"Artifact file missing: {artifact_path}"
    assert ARTIFACTS_ROOT in artifact_path.parents
