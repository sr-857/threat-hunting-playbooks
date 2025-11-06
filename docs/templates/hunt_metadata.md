# Hunt Metadata Standard

Every hunt must include a `hunt.yml` file with the following fields:

| Field | Required | Description |
| --- | --- | --- |
| `id` | ✅ | Globally unique identifier (lowercase snake_case). |
| `name` | ✅ | Human-friendly hunt title. |
| `summary` | ✅ | One-line description of the hunt objective. |
| `entity` | ✅ | Primary entity type (`host`, `user`, `ip`, `hash`, etc.). |
| `owner` | ✅ | Team or analyst group responsible for the hunt. |
| `confidence` | ✅ | Expected confidence level (`low`, `medium`, `high`). |
| `severity` | ✅ | Potential impact (`low`, `medium`, `high`, `critical`). |
| `status` | ✅ | Lifecycle stage (`draft`, `staging`, `production`, `retired`). |
| `version` | ✅ | Semantic version of the hunt definition. |
| `updated_at` | ✅ | ISO8601 date of last update (UTC). |
| `log_sources` | ✅ | List documenting required telemetry, product, service, and prerequisites. |
| `linked_rules` | ✅ | Sigma/YARA references and their use cases. |
| `enrichment` | ✅ | Notebook path, required parameters, and helper scripts/modules. |
| `assumptions` | ✅ | Explicit statements about environment prerequisites. |
| `data_requirements` | ✅ | Telemetry coverage required to run the hunt successfully. |
| `defaults` | ✅ | Default time range, schedule, SLA, comms channel. |
| `attack_mapping` | ✅ | ATT&CK tactics and techniques supported. |
| `tuning_notes` | ✅ | Known sources of noise and mitigation guidance. |
| `variants` | ✅ | Alternate detections or investigative pivots derived from the hunt. |
| `review_checklist` | ✅ | Required steps for analysts before escalation/closure. |
| `notes` | ➕ | Optional implementation references, runbook links, owner notes. |

## Authoring Guidelines

1. **Keep language analyst-friendly.** Avoid opaque shorthand; make each field understandable by someone who did not author the hunt.
2. **Document data quality caveats.** If the hunt breaks without certain enrichments or log fidelity, capture it under `assumptions` or `data_requirements`.
3. **Use variants for supported pivots.** Variants spell out investigation branches instead of implicit knowledge.
4. **Reference enrichment assets.** Link notebooks and helper scripts to ensure repeatable execution.
5. **Version intentionally.** Bump `version` when detection logic, enrichment, or output formats change.

## Example

```yaml
id: win_lateral_movement_wmi
name: Windows Lateral Movement via WMI
entity: host
summary: Detects suspicious remote execution over WMI on Windows endpoints.
owner: secops-hunt-team
confidence: medium
severity: high
status: production
version: 1.0.0
updated_at: 2025-11-06
```

Refer to `hunts/windows_lateral_movement/hunt.yml` for a fully populated sample.
