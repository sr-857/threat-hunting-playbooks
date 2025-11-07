# Example Hunts & Playbooks

This guide curates ready-to-run hunts that ship with the project (or can be added quickly) so analysts can demo capabilities, capture screenshots, and share repeatable workflows.

> **Tip:** Before you begin, ensure the stack is running via `docker compose up --build` and you have a bearer token from `/api/auth/token`.

## Contents

1. [Suspicious PowerShell Execution (built-in)](#suspicious-powershell-execution-built-in)
2. [RDP Brute Force Detection (sample)](#rdp-brute-force-detection-sample)
3. [SaaS Credential Stuffing Campaign](#saas-credential-stuffing-campaign)
4. [Linux SUID Dropper Privilege Escalation](#linux-suid-dropper-privilege-escalation)
5. [Sentinel Connector Abuse](#sentinel-connector-abuse)
6. [Capturing Screenshots for Documentation](#capturing-screenshots-for-documentation)

---

## Suspicious PowerShell Execution (built-in)

| Attribute              | Value |
| --- | --- |
| Playbook ID           | Auto-seeded (`Suspicious PowerShell`)
| ATT&CK Mapping        | TA0008 / TA0002 – T1047 / T1021.006
| Sample Data           | `samples/logs/windows_process.jsonl`
| Rule File             | `rules/windows/suspicious_powershell.yml`
| Run Time              | < 5 seconds on a laptop

### Objective
Detect PowerShell launched with encoded commands—common during lateral movement.

### Steps

#### 1. Launch from the UI
1. Visit `http://localhost:3000` and authenticate with the admin token.
2. Navigate to **Playbooks → Suspicious PowerShell**.
3. Click **Run now**, select the default sample dataset, and confirm.
4. Observe the execution modal and note the telemetry summary once complete.

#### 2. Trigger via CLI
```bash
THREAT_API_URL=http://localhost:8000 \
THREAT_API_TOKEN="<token>" \
threat-cli run "Suspicious PowerShell"
```

#### 3. Validate Results
- Check the **Observability** dashboard for a matching event and alert.
- Inspect `matched_count`, `total_records`, and `confidence` in the response body or telemetry.

> 📸 Capture the run modal and the Observability dashboard after the hunt completes. Store images in `docs/assets/` (see [Capturing Screenshots](#capturing-screenshots-for-documentation)).

### Expected Output Snippet
```json
{
  "playbook": {
    "name": "Suspicious PowerShell",
    "tags": ["windows", "execution", "powershell"]
  },
  "result": {
    "matched_count": 1,
    "total_records": 1,
    "confidence": 1.0,
    "notes": "Local execution against JSONL sample data"
  }
}
```

---

## RDP Brute Force Detection (sample)

Use this template to create a second hunt highlighting authentication telemetry. Populate with internal log samples or test data.

| Attribute              | Value |
| --- | --- |
| Playbook Name         | `Windows RDP Brute Force`
| Suggested ATT&CK      | TA0006 – Credential Access / T1110 – Brute Force
| Sample Data           | `samples/logs/windows_security.jsonl` (create if missing)
| Rule File             | `rules/windows/rdp_bruteforce.yml`
| Tags                  | `windows`, `authentication`, `rdp`

### Rule Skeleton
Save as `rules/windows/rdp_bruteforce.yml`:
```yaml
title: Windows RDP Brute Force
id: aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
status: experimental
description: Detects repeated RDP logon failures followed by a successful login.
logsource:
  product: windows
  service: security
detection:
  selection_fail:
    EventID: 4625
    LogonType: 10
  selection_success:
    EventID: 4624
    LogonType: 10
  timeframe: 5m
  condition: selection_fail | count(user, host) > 5 and selection_success
fields:
  - TargetUserName
  - IpAddress
falsepositives:
  - Jump servers performing legitimate maintenance
level: high
```

### Sample Data Blueprint
Craft a JSONL file (`samples/logs/windows_security.jsonl`) of repeated 4625 events with one 4624 event. Example record:
```json
{"EventID": 4625, "TargetUserName": "administrator", "IpAddress": "203.0.113.40", "LogonType": 10}
```
Repeat the failure record 6–8 times, then append a success entry with `EventID: 4624`.

### Execution
1. In the UI, import the rule via **Playbooks → Add Playbook**, referencing the sample files.
2. Run the hunt using the generated sample data.
3. Capture screenshots of the configuration form and resulting telemetry entry.

> 💡 Highlight how the hunt escalates an alert when the success event follows multiple failures—great for training demos.

---

## SaaS Credential Stuffing Campaign

Demonstrate a modern identity attack where distributed login failures precede a suspicious success that bypasses MFA.

| Attribute | Value |
| --- | --- |
| Playbook Name | `SaaS Credential Stuffing Campaign` |
| Sample Data | `samples/logs/saas_credential_stuffing.jsonl` |
| Hunt Definition | `hunts/saas_credential_stuffing/hunt.yml` |
| Rule File | `rules/sigma/saas/credential_stuffing.yml` |

### Steps
1. Upload the sample JSONL file under **Playbooks → SaaS Credential Stuffing Campaign → Data Sources**.
2. Run the hunt; note `matched_count = 1` and confidence `1.0` from the MFA bypass event.
3. Capture the alert card showing correlated failure and success events.

### Discussion Points
- Explain how distributed IPs indicate credential stuffing versus user error.
- Highlight enrichment from GeoIP and threat intel scripts.
- Encourage analysts to schedule hourly execution and integrate Slack/PagerDuty notifications.

---

## Linux SUID Dropper Privilege Escalation

Showcase Linux endpoint telemetry by correlating chmod events and privileged execution of rogue binaries.

| Attribute | Value |
| --- | --- |
| Playbook Name | `Linux Privilege Escalation via SUID Dropper` |
| Sample Data | `samples/logs/linux_suid_dropper.jsonl` |
| Hunt Definition | `hunts/linux_privilege_escalation/hunt.yml` |
| Rule Files | `rules/sigma/linux/privilege_escalation_suid_dropper.yml`, `rules/yara/linux/suid_dropper.yar` |

### Steps
1. Attach the sample audit log file and run the hunt from the UI.
2. Confirm the telemetry output lists the `kworker` binary with effective UID 0.
3. Demonstrate CLI replay for scripted validation.

### Talking Points
- Discuss tuning allow-lists for configuration management activities.
- Emphasise enrichment scripts mapping binaries to originating users.
- Suggest capturing before/after screenshots of the Observability dashboard.

---

## Sentinel Connector Abuse

Illustrate cloud defense-evasion scenarios by catching automation rule disablement and connector tampering in Azure Sentinel.

| Attribute | Value |
| --- | --- |
| Playbook Name | `Sentinel Connector Abuse` |
| Sample Data | `samples/logs/azure_sentinel_connector_abuse.jsonl` |
| Hunt Definition | `hunts/sentinel_service_abuse/hunt.yml` |
| Rule File | `rules/sigma/cloud/azure_sentinel_connector_abuse.yml` |

### Steps
1. Upload the sample Activity log file and execute the hunt.
2. Validate `matched_count = 3` and review affected connectors in the result payload.
3. Capture the UI timeline illustrating automation rules toggled to disabled.

### Talking Points
- Connect detection to MITRE T1562.008 (Disable/Modify Cloud Logs).
- Explain how the Sentinel connector leverages KQL to correlate operations.
- Recommend follow-up checks: PAM approvals, ingestion metric recovery.

---

## Capturing Screenshots for Documentation

Consistent visuals help contributors understand workflows. Place images in `docs/assets/` and reference them with relative paths.

| Screenshot | Suggested Filename | Capture Notes |
| --- | --- | --- |
| Playbook run confirmation modal | `playbook-run-modal.png` | Trigger a quick run from the UI and capture the success state. |
| Observability dashboard alert tile | `observability-alert-tile.png` | After a hunt runs, capture the Alerts section showing the new entry. |
| Telemetry JSON in Swagger | `telemetry-events.png` | Use Swagger at `/docs` to show the `/telemetry/events` response. |
| CLI demo summary | `demo-cli-summary.png` | Run `make demo` and screenshot the final terminal summary block. |

Embed screenshots in Markdown:
```markdown
![Observability dashboard](../assets/observability-dashboard.png)
```

> Refer to `docs/assets/README.md` for the full catalogue of recommended filenames and hygiene tips when adding new images.

> Store source images (if any) in a shared folder or design tool so they can be updated without pixelation. Keep sensitive data masked or use synthetic samples.

---

### Next Ideas
- Add Linux or cloud-focused hunts alongside Windows examples.
- Record short GIFs of the run workflow using tools like `asciinema` or `peek`.
- Link to Discussions threads where analysts can request new hunts or share tuning tips.
