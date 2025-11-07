# Linux Persistence: Cron-based Backdoor

This playbook demonstrates how to detect adversaries that establish persistence on Linux hosts by planting cron jobs that execute suspicious payloads.

| Attribute | Value |
| --- | --- |
| Category | Linux |
| ATT&CK Mapping | TA0003 – Persistence / T1053.003 – Scheduled Task/Job: Cron |
| Data Sources | Syslog, auditd, cron logs |
| Sample File | `samples/logs/linux_cron.jsonl` |
| Rule File | `rules/linux/cron_persistence.yml` |
| Tags | `linux`, `persistence`, `cron` |

## Analyst Narrative
1. Threat actor gains shell access and writes a payload to `/tmp/x`.
2. Actor modifies the root crontab to run `/tmp/x` every minute using an encoded bash command.
3. SOC collects syslog and auditd events that record crontab creation and execution attempts.
4. The hunt surfaces rapid-fire cron executions tied to the suspicious script.

## Detection Logic
```yaml
title: Linux Cron Persistence Backdoor
id: 6c1a5f7d-7e8c-4dd0-8f8f-5e0b11afdf58
status: experimental
description: Detects cron jobs invoking writable paths or encoded payloads.
logsource:
  product: linux
  service: syslog
detection:
  selection:
    message|contains:
      - "CRON" 
      - "(root)"
  filter_tmp:
    message|contains:
      - "/tmp/"
      - "base64"
  condition: selection and filter_tmp
fields:
  - user
  - command
falsepositives:
  - Legitimate admin scripts placed in `/tmp`
level: high
```

> Adjust the detection to match your logging format. For auditd, pivot on `audit(.*CRON)` events and the `cmd` field.

## Sample Data Blueprint
```json
{"timestamp": "2025-05-01T10:00:00Z", "message": "CRON[1234]: (root) CMD=(/usr/bin/base64 -d /tmp/.c | /bin/bash)"}
{"timestamp": "2025-05-01T10:01:00Z", "message": "CRON[1235]: (root) CMD=(/tmp/x)"}
```
Load 5–10 entries into `samples/logs/linux_cron.jsonl` alongside benign cron jobs to test filtering.

## Execution Guide
1. **Import** the rule into the UI via **Playbooks → Add Playbook**.
2. **Associate** the sample dataset when prompted or upload real syslog exports.
3. **Run** the hunt on demand or configure a 15-minute schedule for continuous monitoring.

## Telemetry & Tuning
- Highlight counts by `command` to spot novel payload paths.
- Tune false positives by whitelisting known maintenance scripts.
- Combine with file-integrity telemetry to confirm `/tmp/x` creation.

## Screenshot Ideas
- Playbook configuration form showing rule metadata.
- Observability dashboard entry with elevated confidence.
- Grafana panel plotting cron executions per host.

## Follow-up Actions
- Contain the host and remove the malicious cron entry.
- Rotate credentials used on the host.
- Expand hunt to detect similar behaviour across the fleet.
