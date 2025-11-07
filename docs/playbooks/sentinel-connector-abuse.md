# Sentinel Connector Abuse

> Sample data: `samples/logs/azure_sentinel_connector_abuse.jsonl`

Monitor suspicious configuration changes targeting Microsoft Sentinel data connectors and automation rules to prevent blind spots.

| Attribute | Value |
| --- | --- |
| Category | Azure / SIEM |
| ATT&CK | TA0005 – Defense Evasion; TA0007 – Discovery |
| Technique | T1562.008 – Disable or Modify Cloud Logs |
| Sample Playbook | `hunts/sentinel_service_abuse/hunt.yml` |
| Sigma Rule | `rules/sigma/cloud/azure_sentinel_connector_abuse.yml` |

## Scenario Walkthrough
1. Compromised automation service principal updates ingestion connectors to a disabled state.
2. Automation rule responsible for escalations is patched to `enabled = false`.
3. Sentinel ingestion metrics dip, but no alert triggers without this hunt.
4. Hunt surfaces correlated operations within the same actor and short timeframe, flagging potential tampering.

## Data Requirements
- Azure Activity logs for Microsoft Sentinel resource operations.
- Diagnostic logs capturing data connector status changes (`properties.ingestionStatus`).
- Optional: Log Analytics workspace metrics for ingestion volume baselines.

## Detection Logic Snapshot
```yaml
condition: selection_connector_disable or selection_automation_disable
```
Sigma rule keys on operations modifying connectors or automation rules with disabled states.

## Execution
### Local replay
```bash
THREAT_API_URL=http://localhost:8000 \
THREAT_API_TOKEN="$TOKEN" \
threat-cli run sentinel_service_abuse \
  --input samples/logs/azure_sentinel_connector_abuse.jsonl
```

### Sentinel Connector
1. Configure Sentinel connector credentials (`SENTINEL_WORKSPACE_ID`, `SENTINEL_TENANT_ID`, `SENTINEL_CLIENT_ID`, `SENTINEL_CLIENT_SECRET`).
2. Ensure Azure Activity logs are streamed to the Log Analytics workspace.
3. Hunt issues KQL query correlating `MICROSOFT.SECURITYINSIGHTS/DATACONNECTORS` and `AUTOMATIONRULES` operations.

### Splunk / Elastic
- Stream Azure Activity logs through existing pipelines; update index mapping to include `Properties.enabled` and `Properties.ingestionStatus` fields.
- Connector executes SPL or DSL queries reusing Sigma selection.

## Validation Artifacts
- **Telemetry:** `telemetry/hunt_events.jsonl` displays `matched_count = 3` with actor `spn-automation-001`.
- **UI Evidence:** Alert card screenshot showing connector disablement timeline.
- **Connector Replay:** Stored query response verifying detection in Sentinel.

## Analyst Checklist
- Validate actor principal against privileged access register.
- Review change management tickets covering Sentinel maintenance.
- Re-enable connectors or automation rules, and monitor ingestion recovery.

## Tuning & Variants
- Allow-list maintenance windows by tagging actor principals during scheduled updates.
- Variant: focus on data connector deletion events (`DELETE`) to catch destructive changes.
