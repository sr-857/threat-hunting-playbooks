# SaaS Credential Stuffing Campaign

> Sample data: `samples/logs/saas_credential_stuffing.jsonl`

Detect rapid, distributed login failures followed by success that indicates compromised SaaS accounts and MFA bypass.

| Attribute | Value |
| --- | --- |
| Category | SaaS / Identity |
| ATT&CK | TA0006 – Credential Access; TA0001 – Initial Access |
| Technique | T1110 – Brute Force; T1078 – Valid Accounts |
| Sample Playbook | `hunts/saas_credential_stuffing/hunt.yml` |
| Sigma Rule | `rules/sigma/saas/credential_stuffing.yml` |

## Scenario Walkthrough
1. An attacker replays stolen credentials across multiple IPs.
2. The identity provider logs repeated `failure` results within seconds.
3. Minutes later the same account authenticates successfully without MFA challenge.
4. The hunt correlates failures and success to raise a high-confidence alert.

## Data Requirements
- Authentication audit logs with fields: `user`, `sourceIpAddress`, `userAgent`, `outcome`, `mfaResult`.
- Optional enrichment: GeoIP location metadata, threat intel tagging for source IPs.

## Detection Logic Snapshot
```yaml
condition: selection_failures | count(>=5) by user | near selection_success by user within 5m
```
The rule aggregates failures per user and looks for a neighbouring success within five minutes.

## Execution
### Local replay
```bash
THREAT_API_URL=http://localhost:8000 \
THREAT_API_TOKEN="$TOKEN" \
threat-cli run saas_credential_stuffing \
  --input samples/logs/saas_credential_stuffing.jsonl
```

### Splunk
1. Configure Splunk connector credentials in `.env` (`SPLUNK_BASE_URL`, token or username/password).
2. Load SaaS audit logs into an index (e.g., `saas_audit`).
3. Run the hunt; connector translates the Sigma selection and issues an SPL search over the time window.

### Elastic
1. Point Elastic connector to the auditbeat-style index storing SaaS sign-ins.
2. Ensure `outcome` and `mfaResult` are keyword fields.
3. Use runtime fields to normalise location data if required.

## Validation Artifacts
- **Screenshots:** UI alert card showing failure burst + success pivot.
- **Logs:** `telemetry/hunt_events.jsonl` contains `matched_count = 1` for the sample dataset.
- **Connector Replay:** Capture Splunk job export payload demonstrating matched record.

## Analyst Checklist
- Verify account ownership and MFA status.
- Pivot to SaaS admin logs for password reset, token creation, or delegated admin grants.
- Initiate forced password reset and session revocation if malicious.

## Tuning & Variants
- Increase failure threshold for large tenants to avoid noisy users.
- Add blocklists for corporate VPN ranges to prevent false positives.
- Variant: monitor legacy protocols (`IMAP`, `POP`, `SMTP`) lacking MFA.
