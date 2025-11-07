# OT Network Reconnaissance

> Sample data: `samples/logs/ot_network_recon.jsonl`

Expose reconnaissance targeting industrial control systems (ICS) by correlating ladder logic enumeration and historian data pulls.

| Attribute | Value |
| --- | --- |
| Category | Operational Technology |
| ATT&CK for ICS | TA0100 – Device Access; TA0102 – Network Discovery |
| Techniques | T0840 – Module Enumeration; T0843 – Program Upload; T0830 – Network Sniffing |
| Playbook | `hunts/ot_network_recon/hunt.yml` |
| Sigma Rule | `rules/sigma/ot/network_recon_ladder_logic.yml` |

## Scenario Walkthrough
1. An internal workstation at `10.10.5.23` enumerates PLC blocks via S7comm (`ListBlocks`).
2. The same host issues `ReadSZL` (System Status List) to fingerprint firmware/modules.
3. An `Upload` request follows, denied by the PLC due to access restrictions.
4. Minutes later, the actor pivots to the historian, downloading 500 tags to map OT assets.
5. Hunt correlates the sequence and raises a critical alert for OT defender action.

## Data Requirements
- Zeek ICS (or equivalent) capturing S7 protocol metadata (`query_function`, `plc_address`).
- Historian audit logs (OSIsoft PI, GE Proficy) for tag browse/download operations.
- Optional firewall logs to validate cross-zone policy violations.

## Detection Logic Snapshot
```yaml
condition: selection_list_blocks and selection_read_szl and selection_upload within 5m
```
The Sigma rule focuses on a rapid sequence of ladder logic discovery followed by attempted upload.

## Execution
### Local replay
```bash
THREAT_API_URL=http://localhost:8000 \
THREAT_API_TOKEN="$TOKEN" \
threat-cli run ot_network_recon \
  --input samples/logs/ot_network_recon.jsonl
```

### Splunk
1. Ingest Zeek ICS logs into `ot_ics` index with fields for `protocol`, `query_function`, `plc_address`.
2. Stream historian audit logs into `ot_historian` index.
3. Hunt executes via Splunk connector, using transactions to correlate functions within 5 minutes.

### Elastic
1. Index ICS telemetry into `ot-ics-*` with ECS-aligned fields (`event.category: network`, `ics.protocol`).
2. Hunt generates an Elasticsearch DSL query that chains multiple protocol events per source IP.
3. Historian events are joined in the enrichment notebook for analyst triage.

## Enrichment & Analysis
- Notebook `notebooks/enrichment/ot_network_recon.ipynb` visualises ladder logic requests and historian pulls.
- Asset context script cross-references `plc_address` with `scripts/lib/context/ot_assets.py` for criticality.
- IP reputation enrichment flags whether the source host resides in approved maintenance range.

## Analyst Conclusion Checklist
- ✅ Is the source host authorized for engineering tasks in this zone?
- ✅ Were similar requests executed by scheduled maintenance jobs?
- ✅ Did any follow-up write/program upload events succeed?
- ✅ Are there concurrent alerts on the same asset (e.g., firewall denies, endpoint alerts)?

## Tuning & Variants
- Suppress known historian backup jobs by tagging service accounts.
- Extend detection to Modbus (function codes 1–4) or OPC-UA browse storms.
- Use scheduled OT maintenance calendars to automatically mute alerts during approved windows.
