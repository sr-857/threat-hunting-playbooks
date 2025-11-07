# Day-One Guided Hunt

A field guide for analysts logging in for the first time. Follow these steps to run a complete hunt, validate outputs, and understand where to pivot next.

## 1. Prepare Your Environment
- Ensure `docker compose up --build` is running all services.
- Obtain an admin token via `/api/auth/token` (see [Getting Started](../getting-started.md#authenticate-as-the-initial-admin)).
- Install the CLI locally:
  ```bash
  cd cli
  pip install .
  ```

## 2. Log Into the UI
1. Navigate to `http://localhost:3000` and enter the admin credentials.
2. On the welcome screen, click **Playbook Gallery**. Confirm at least four ready-to-run hunts are visible.

> If you see no playbooks, verify the API container logs for seeding errors and re-run `docker compose up`.

## 3. Import Sample Telemetry
We will use the **SaaS Credential Stuffing** playbook for this walkthrough.
1. From the UI, open **Playbooks → SaaS Credential Stuffing Campaign**.
2. Click **Add Sample Data** and upload `samples/logs/saas_credential_stuffing.jsonl`.
3. Confirm the file appears under **Data Sources** with 4 records.

## 4. Run the Hunt
1. Click **Run Now**.
2. Select the uploaded sample dataset and choose **Run Immediately**.
3. Observe the execution modal; when it finishes, note the run ID and matched count.
4. The CLI equivalent:
   ```bash
   THREAT_API_URL=http://localhost:8000 \
   THREAT_API_TOKEN="$TOKEN" \
     threat-cli run saas_credential_stuffing \
       --input samples/logs/saas_credential_stuffing.jsonl
   ```

## 5. Validate Output
- **Observability Dashboard:** Navigate to **Observability → Hunts** and locate the latest entry. Confirm the confidence score is `1.0` and the matched event lists the bypassed MFA.
- **Telemetry API:** Visit `http://localhost:8000/docs#/Telemetry/get_telemetry__events` and execute the request with the admin token. Ensure the hunt run appears with correct playbook ID and timestamps.
- **Artifacts:** Check `logs/output/saas_credential_stuffing/` for a JSON summary.

> If no results appear, verify the sample data path and confirm the hunt ID exactly matches `saas_credential_stuffing`.

## 6. Pivot and Triage
1. From the alert card, use the **Enrichment** tab to view GeoIP and IP reputation context provided by the playbook notebook.
2. Review the **Next Actions** checklist: password reset, session revocation, incident ticket creation.
3. Open the linked [Day-One Playbook Checklist](../templates/day-one-playbook-checklist.md) (create if missing) to record findings.

## 7. Extend the Scenario
- Import real SaaS audit logs for staging environments and rerun the hunt.
- Adjust the threshold from `>=5` failures to match tenant volume.
- Schedule the hunt hourly via CLI:
  ```bash
  threat-cli schedules create \
    --name "Hourly SaaS Credential Stuffing" \
    --playbook saas_credential_stuffing \
    --cron "0 * * * *"
  ```

## 8. Troubleshooting Quick Reference
| Symptom | Resolution |
| --- | --- |
| Hunt run fails with `401` | Token expired—refresh via `/api/auth/token`. |
| UI shows no telemetry | Confirm worker container logs (`docker compose logs worker`). |
| Sample data upload stuck | Ensure the `samples/logs` directory is mounted; restart the API container. |

## 9. Next Steps
- Proceed to [Linux SUID Dropper](../playbooks/linux-suid-dropper.md) for endpoint telemetry validation.
- Review [Connector Validation Matrix](../connectors/validation.md) to plan production integrations.
- Share feedback or questions in the `#threat-playbooks` discussion thread.
