# Example Hunts & Playbooks

This guide curates ready-to-run hunts that ship with the project (or can be added quickly) so analysts can demo capabilities, capture screenshots, and share repeatable workflows.

> **Tip:** Before you begin, ensure the stack is running via `docker compose up --build` and you have a bearer token from `/api/auth/token`.

## Contents

1. [Suspicious PowerShell Execution (built-in)](#suspicious-powershell-execution-built-in)
2. [RDP Brute Force Detection (sample)](#rdp-brute-force-detection-sample)
3. [Capturing Screenshots for Documentation](#capturing-screenshots-for-documentation)

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

## Capturing Screenshots for Documentation

Consistent visuals help contributors understand workflows. Place images in `docs/assets/` and reference them with relative paths.

| Screenshot | Suggested Filename | Capture Notes |
| --- | --- | --- |
| Playbook run confirmation modal | `playbook-run-modal.png` | Trigger a quick run from the UI and capture the success state. |
| Observability dashboard alert tile | `observability-dashboard.png` | After a hunt runs, capture the Alerts section showing the new entry. |
| Telemetry JSON in Swagger | `telemetry-api-response.png` | Use Swagger at `/docs` to show the `/telemetry/events` response. |

Embed screenshots in Markdown:
```markdown
![Observability dashboard](../assets/observability-dashboard.png)
```

> Store source images (if any) in a shared folder or design tool so they can be updated without pixelation. Keep sensitive data masked or use synthetic samples.

---

### Next Ideas
- Add Linux or cloud-focused hunts alongside Windows examples.
- Record short GIFs of the run workflow using tools like `asciinema` or `peek`.
- Link to Discussions threads where analysts can request new hunts or share tuning tips.
