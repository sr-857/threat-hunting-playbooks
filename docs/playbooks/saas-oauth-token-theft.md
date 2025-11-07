# SaaS OAuth Token Theft Investigation

> Sample data: `samples/logs/saas_oauth_token_theft.jsonl`

Detect refresh token grants from anomalous devices that bypass MFA and quickly pivot to sensitive API calls.

| Attribute | Value |
| --- | --- |
| Category | SaaS / Identity |
| ATT&CK | TA0001 – Initial Access; TA0006 – Credential Access; TA0003 – Persistence |
| Techniques | T1528 – Steal Application Access Token; T1550.001 – Alternate Authentication Material |
| Playbook | `hunts/saas_oauth_token_theft/hunt.yml` |
| Sigma Rule | `rules/sigma/saas/oauth_token_theft.yml` |

## Scenario Walkthrough
1. Adversary reuses a harvested refresh token against the SaaS IdP.
2. MFA is not challenged because the session is considered trusted.
3. The same client immediately downloads sensitive files through an API endpoint.
4. Hunt correlates the anomalous grant with downstream API usage to flag likely compromise.

## Data Requirements
- OAuth grant audit logs with `grantType`, `mfaDetail`, `ipAddress`, and device metadata.
- API gateway logs for the same principal within ±10 minutes.
- Optional CASB or risk scoring metadata to enrich IP reputation.

## Detection Logic Snapshot
```yaml
condition: selection_grant or selection_risk
```
The Sigma rule highlights refresh token grants without MFA or with anomalous risk details.

## Execution
### Local replay
```bash
THREAT_API_URL=http://localhost:8000 \
THREAT_API_TOKEN="$TOKEN" \
threat-cli run saas_oauth_token_theft \
  --input samples/logs/saas_oauth_token_theft.jsonl
```

### Splunk
1. Index identity telemetry into `saas_identity`.
2. Configure the Splunk connector environment variables and ensure fields are normalized.
3. Hunt issues SPL to retrieve suspicious grants and joins against API usage logs.

### Elastic
1. Ingest audit logs into an index pattern such as `saas-audit-*`.
2. Provide ECS-compatible fields for `event.category`, `client.ip`, and `mfaDetail`.
3. Run the playbook; the connector translates Sigma filters into Elasticsearch DSL.

## Enrichment & Analysis
- Threat intel script enriches IP addresses with reputation verdicts.
- Notebook `notebooks/enrichment/saas_oauth_token_threat.ipynb` maps token grants to subsequent API calls.
- Analysts confirm whether the client device is registered or corporate managed.

## Analyst Conclusion Checklist
- ✅ Was the refresh token issued to a trusted application and redirect URI?
- ✅ Did the user expect access from the observed device/geo?
- ✅ Were sensitive APIs accessed using the same token within minutes?
- ✅ Have sessions been revoked and credentials reset?

## Tuning & Variants
- Allow-list corporate headless clients that legitimately renew tokens without MFA.
- Tune anomaly thresholds for known VPN exit IP ranges.
- Variant: detect `grantType=password` or `client_credentials` flows unexpectedly mapped to user principals.
