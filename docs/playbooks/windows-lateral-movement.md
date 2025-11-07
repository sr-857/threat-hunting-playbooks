# Windows Lateral Movement via WMI

> See also: [Linux Cron Persistence](./linux-persistence.md) · [Cloud IAM Impossible Travel](./cloud-iam-anomalies.md)

This walkthrough explains the intent, data requirements, execution flow, and analyst review steps for the `win_lateral_movement_wmi` hunt.

## Objective

Detect suspicious remote execution activity using Windows Management Instrumentation (WMI) that may indicate lateral movement across hosts.

## Hunt Metadata

| Field | Value |
| --- | --- |
| Hunt ID | `win_lateral_movement_wmi` |
| Entity | Host |
| Severity | High |
| Confidence | Medium |
| Version | 1.0.0 |
| ATT&CK | [T1047](https://attack.mitre.org/techniques/T1047/), [T1021.006](https://attack.mitre.org/techniques/T1021/006/) |
| Linked Rule | `rules/sigma/windows/lateral_movement_wmi.yml` |

Full metadata is available in `hunts/windows_lateral_movement/hunt.yml`.

## Data Requirements

- Windows Security Event IDs 4688, 4689, 4672 from target hosts and suspected source systems.
- Sysmon Event ID 1 for detailed process command lines.
- Active Directory or CMDB data to map user → host relationships (optional enrichment).

Ensure Sigma translation and sample data paths in the hunt configuration point to accessible locations in your environment.

## Execution Flow

1. **Sigma evaluation**: The playbook runs the `lateral_movement_wmi.yml` Sigma rule against JSONL process logs (local sample or connector output).
2. **Match scoring**: Each record is assessed; `matched_count / total_records` becomes the confidence ratio.
3. **Artifacts**: Results are persisted to `logs/output/<playbook_id>/result_<timestamp>.json` along with summary details.
4. **Telemetry**: Hunt runs feed structured events into `telemetry/hunt_events.jsonl` and the Observability dashboard; high-confidence runs emit alerts if they exceed the configured threshold.

## Analyst Review Checklist

- Validate that the originating host/user combination is unexpected for the target system.
- Inspect command-line arguments for remote execution flags (`/node:`, `-ComputerName`).
- Cross-reference enrichment notebook output (`notebooks/enrichment/windows_remote_execution.ipynb`) for logged-on user data and network shares.
- Confirm with endpoint telemetry (EDR) before escalating to an incident.

## Tuning Ideas

- Baseline known remote administration tools (SCCM, PDQ Deploy) and allow-list their service accounts.
- Raise `ALERT_CONFIDENCE_THRESHOLD` if manual review indicates frequent false positives.
- Expand coverage by enabling the `WMI with Encoded Commands` variant—focuses on PowerShell’s `-encodedcommand` usage combined with WMI.

## Running the Hunt

### On-demand via CLI

```bash
THREAT_API_URL=http://localhost:8000 \
THREAT_API_TOKEN="<token>" \
threat-cli run <playbook-id>
```

The CLI prints the run summary and stores telemetry for later review.

### Scheduled Execution

Create an hourly schedule using the CLI:

```bash
threat-cli schedules create \
  --name "Hourly WMI Lateral Hunt" \
  --playbook <playbook-id> \
  --cron "0 * * * *"
```

The Celery worker will execute the hunt on schedule, update next-run metadata, and surface results in the Observability dashboard.

## Follow-on Actions

- Enrich matched hosts with asset criticality and user role information.
- Escalate confirmed malicious activity into the SOC case management system using the manual integration checklist (`docs/templates/soc_integration.md`).
- Feed findings back into the ATT&CK coverage matrix to track detection efficacy over time.
