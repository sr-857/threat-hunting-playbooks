# Linux SUID Dropper Privilege Escalation

> Sample data: [`samples/logs/linux_suid_dropper.jsonl`](../samples/logs/linux_suid_dropper.jsonl)

Identify actors compiling or dropping setuid binaries to escalate privileges on Linux hosts.

| Attribute | Value |
| --- | --- |
| Category | Linux Endpoint |
| ATT&CK | TA0004 – Privilege Escalation; TA0006 – Credential Access |
| Technique | T1548 / T1548.001 – Abuse Elevation Control Mechanism (Setuid) |
| Sample Playbook | `hunts/linux_privilege_escalation/hunt.yml` |
| Sigma Rule | `rules/sigma/linux/privilege_escalation_suid_dropper.yml` |
| YARA Rule | `rules/yara/linux/suid_dropper.yar` |

## Scenario Walkthrough
1. Web shell drops a binary under `/tmp/.cache/.sshd_helper` and compiles it with `gcc`.
2. The binary is moved into `/usr/local/bin/kworker` and marked setuid (`chmod 4755`).
3. Adversary executes the binary, inheriting root privileges to pivot further.
4. Hunt correlates the permission change and privileged execution within 10 minutes.

## Data Requirements
- Linux Auditd records for `chmod`, `execve`, and `rename` events.
- Endpoint telemetry capturing parent process lineage (e.g., `gcc` → `chmod`).
- Optional file integrity monitoring data for newly created binaries.

## Detection Logic Snapshot
```yaml
condition: selection_chmod | followedby selection_exec within 10m
```
The Sigma logic looks for a chmod setting the SUID bit followed by execution of the resulting binary with effective UID 0.

## Execution
### Local replay
```bash
THREAT_API_URL=http://localhost:8000 \
THREAT_API_TOKEN="$TOKEN" \
threat-cli run linux_privilege_escalation \
  --input samples/logs/linux_suid_dropper.jsonl
```

### Elastic
1. Configure the Elastic connector credentials in `.env` (`ELASTIC_ENDPOINT`, `ELASTIC_API_KEY`).
2. Index audit logs into `auditbeat-*` with fields for `process.executable`, `process.effective.uid`, and `file.mode`.
3. The connector translates the Sigma selection and submits an EQL-style query to Elastic, constrained to the playbook’s time range.

### Splunk
1. Enable the Splunk connector with HEC token or username/password.
2. Ingest audit logs into `linux_audit`. The hunt issues SPL similar to:
   ```spl
   search file_mode=4755 action=chmod | transaction host process maxspan=10m | search euid=0
   ```
3. Verify the resulting events appear in the Observability dashboard.

## Validation Artifacts
- **Telemetry:** `telemetry/hunt_events.jsonl` shows `matched_count = 2` with host `web-03`.
- **Sample Output:** Saved to `logs/output/linux_privilege_escalation/result_<timestamp>.json` with executable path reference.
- **Screenshots:** CLI output and UI alert timeline with enrichment pivots.

## Analyst Checklist
- Confirm binary hash against golden images or package repositories.
- Investigate how the binary was introduced (upload / compile / package manager).
- Review privilege escalations post-execution (new users, modified sudoers).

## Tuning & Variants
- Allow-list legitimate SUID binaries deployed via configuration management.
- Lower alert sensitivity for maintenance windows with known deployments.
- Variant: monitor `/etc/sudoers` modifications and `chmod` events granting `NOPASSWD`.
