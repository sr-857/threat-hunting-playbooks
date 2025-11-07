# Connector Validation Matrix

Evidence that each supported connector has been exercised against realistic datasets. Use this matrix to decide when a connector is production-ready and what gaps remain.

| Connector | Dataset | Validation Method | Assertions | Last Run |
| --- | --- | --- | --- | --- |
| Splunk | `samples/logs/windows_security.jsonl` (RDP brute force) | Replay via `/services/search/jobs/export` using integration test harness | Query returns ≥1 event; timestamps parsed; `ExecutionResult.records` populated | 2025-11-07 |
| Splunk | `samples/logs/saas_credential_stuffing.jsonl` | CLI replay against search head with synthetic data | Counts failures vs. success; validates alert metadata fields | 2025-11-07 |
| Elastic | `samples/logs/linux_suid_dropper.jsonl` indexed into `auditbeat-*` | Pytest integration using Elastic docker container | Range filter applied; results include `process.executable` and `@timestamp` | 2025-11-07 |
| Elastic | `samples/logs/cloud_signins.jsonl` (Impossible Travel) | Manual replay via Kibana dev tools; connector fetch | Geolocation enrichment fields preserved | 2025-11-06 |
| Sentinel | `samples/logs/azure_sentinel_connector_abuse.jsonl` | KQL replay with `LogsQueryClient` in dev tenant | `MICROSOFT.SECURITYINSIGHTS/*` operations correlated in same timespan | 2025-11-07 |
| Sentinel | Live workspace (Contoso lab) | Runbook triggered automation change and restored baseline | Alert triggered within 2 min; automation rule re-enabled | 2025-11-05 |

## How to Reproduce

### Splunk Connector
1. Set environment variables:
   ```env
   SPLUNK_BASE_URL=https://splunk.lab:8089
   SPLUNK_TOKEN=<hec-token>
   ```
2. Load sample dataset:
   ```bash
   curl -k -u admin:password https://splunk.lab:8089/servicesNS/admin/search/data/inputs/oneshot \
     -d name=@samples/logs/saas_credential_stuffing.jsonl
   ```
3. Execute pytest scenario:
   ```bash
   pytest tests/connectors/test_splunk_integration.py
   ```

### Elastic Connector
1. Export sample data into Elastic:
   ```bash
   elasticsearch-loader --index auditbeat-test samples/logs/linux_suid_dropper.jsonl
   ```
2. Run validation:
   ```bash
   pytest tests/connectors/test_elastic_integration.py
   ```
3. Confirm output stored in `logs/output/linux_privilege_escalation/`.

### Sentinel Connector
1. Configure secrets in `.env`:
   ```env
   SENTINEL_WORKSPACE_ID=<workspace>
   SENTINEL_TENANT_ID=<tenant>
   SENTINEL_CLIENT_ID=<app-id>
   SENTINEL_CLIENT_SECRET=<secret>
   ```
2. Upload sample Activity logs via Azure CLI:
   ```bash
   az monitor log-analytics workspace data-export create \
     --resource-group rg-lab \
     --workspace-name contoso-workspace \
     --destination data/azure_sentinel_connector_abuse.jsonl
   ```
3. Trigger validation:
   ```bash
   pytest tests/connectors/test_sentinel_integration.py
   ```

## Open Items
- Automate dataset replay via GitHub Actions self-hosted runners with mocked endpoints.
- Expand coverage for connector pagination and error-handling scenarios.
- Document live customer datasets once permitted under data-sharing agreements.
