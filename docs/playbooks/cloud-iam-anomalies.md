# Cloud IAM Anomalies: Impossible Travel Sign-in

Detect identity provider events indicating that a single user authenticates from two distant geographies within an impossible time window.

| Attribute | Value |
| --- | --- |
| Category | Cloud |
| ATT&CK Mapping | TA0001 – Initial Access / T1078 – Valid Accounts |
| Data Sources | Cloud audit logs (Azure AD, Okta, AWS CloudTrail) |
| Sample File | `samples/logs/cloud_signins.jsonl` |
| Rule File | `rules/cloud/iam_impossible_travel.yml` |
| Tags | `cloud`, `iam`, `authentication` |

## Scenario Overview
1. User `alex.m` successfully signs in from New York at 09:00 UTC.
2. At 09:05 UTC the same user signs in from Singapore.
3. The IdP emits an `ImpossibleTravel` flag in the event metadata.
4. Hunt surfaces the event pair and creates a high-confidence alert.

## Detection Logic
```yaml
title: Cloud IAM Impossible Travel
id: 9d5d2c3b-6ea4-44d9-920d-3f07b715ef20
status: stable
description: Detects authentication attempts flagged as impossible travel by the identity provider.
logsource:
  product: cloud
  service: iam
detection:
  selection:
    riskType: "ImpossibleTravel"
  condition: selection
fields:
  - userPrincipalName
  - city
  - country
  - timestamp
falsepositives:
  - VPN providers that exit through distant regions
level: medium
```

> Some providers emit a `riskLevel` or `anomalyType` field instead of `riskType`. Adjust the detection to align with your schema.

## Sample Data Blueprint
```json
{"timestamp": "2025-07-01T09:00:00Z", "userPrincipalName": "alex.m@example.com", "city": "New York", "country": "US", "riskType": "ImpossibleTravel"}
{"timestamp": "2025-07-01T09:05:00Z", "userPrincipalName": "alex.m@example.com", "city": "Singapore", "country": "SG", "riskType": "ImpossibleTravel"}
```

## Execution Guide
1. Upload or reference `cloud_signins.jsonl` when creating the playbook.
2. Set the schedule to 5 minutes to catch near real-time anomalies.
3. Notify downstream teams via Slack or PagerDuty integration configured in `app/core/config.py`.

## Telemetry & Tuning
- Include scatter plots of login locations in Grafana or the UI dashboard for visual confirmation.
- Whitelist corporate VPN exit IPs to dampen false positives.
- Elevate severity when the account is privileged or MFA is bypassed.

## Screenshot Ideas
- UI screenshot showing an alert card with the two locations highlighted.
- Swagger response snippet from `/api/telemetry/alerts` containing the risk event.

## Response Checklist
- Confirm whether the sign-in was legitimate by contacting the user.
- Force password reset and revoke tokens if malicious.
- Hunt for associated actions (resource creation, abnormal API calls) in CloudTrail.
