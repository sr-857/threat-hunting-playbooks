# Windows RDP Brute Force Detection

Detect brute-force activity against Remote Desktop Protocol by spotting multiple failed logons followed by a success event.

| Attribute | Value |
| --- | --- |
| Category | Windows |
| ATT&CK Mapping | TA0006 – Credential Access / T1110 – Brute Force |
| Sample Data | `samples/logs/windows_security.jsonl` |
| Rule File | `rules/windows/rdp_bruteforce.yml` |
| Tags | `windows`, `authentication`, `rdp` |

## Detection Logic
```yaml
title: Windows RDP Brute Force
id: 7f2b7560-1bd3-45f5-b02f-7d56f0c4d3cf
status: experimental
description: Detects repeated RDP logon failures followed by a success.
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
  condition: selection_fail | count(TargetUserName, IpAddress) >= 5 and selection_success
fields:
  - TargetUserName
  - IpAddress
falsepositives:
  - Administrative maintenance using service accounts
level: high
```

## Execution Guide
1. Import the rule via **Playbooks → Add Playbook**.
2. Upload or reference `samples/logs/windows_security.jsonl`.
3. Run the hunt and monitor the Observability dashboard for the resulting alert.

## Analyst Tips
- Correlate results with firewall logs or endpoint telemetry to confirm success.
- Reset credentials or enforce MFA when brute-force activity is detected.
- Add exclusions for known penetration-testing sources if necessary.
