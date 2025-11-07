# Tutorial: Run Your First Hunt

This short tutorial walks you from a fresh clone to validating a successful hunt execution. Expect to spend about 10 minutes.

> **Prerequisites**
> - Docker Engine ≥ 24 and Docker Compose ≥ 2.20
> - Node.js 18+ and npm 9+
> - Python 3.11+
> - (Optional) `make`, `jq`, `yq` for scripting helpers

---

## 1. Clone and Install Dependencies

```bash
git clone https://github.com/sr-857/threat-hunting-playbooks.git
cd threat-hunting-playbooks

# Install UI dependencies once for linting/builds
cd ui
npm install
cd ..
```

---

## 2. Launch the Stack

```bash
docker compose up --build
```

This starts the FastAPI service, Next.js UI, Celery workers, Redis, PostgreSQL, MinIO, Prometheus, and Grafana.

| Service | URL | Purpose |
| --- | --- | --- |
| UI | `http://localhost:3000` | Analyst dashboard and catalog |
| API | `http://localhost:8000/api` | JWT-secured REST API |
| Swagger | `http://localhost:8000/docs` | API explorer |
| Prometheus | `http://localhost:9090` | Metrics scraping |
| Grafana | `http://localhost:3001` | Dashboards |

> Keep the compose stack running in a terminal while you continue.

---

## 3. Obtain an Admin Token

The bootstrap process seeds an administrator (defaults: `admin@example.com` / `ChangeMe123!`). Request an access token:

```bash
curl -X POST http://localhost:8000/api/auth/token \
  -H 'Content-Type: application/x-www-form-urlencoded' \
  -d 'username=admin@example.com&password=ChangeMe123!'
```

Copy the `access_token` value. Export it for convenience:

```bash
export THREAT_API_URL=http://localhost:8000
export THREAT_API_TOKEN="<copied token>"
```

---

## 4. Explore the Catalog

Visit `http://localhost:3000` and sign in using the admin credentials. Open **Playbooks → Suspicious PowerShell** to review metadata, sample files, and ATT&CK mappings.

> 📸 Capture a screenshot of the playbook detail panel for reference.

---

## 5. Execute the Hunt

### Option A: From the UI
1. Click **Run now**.
2. Accept the default sample dataset (`windows_process.jsonl`).
3. Confirm the run and wait for the modal to report success.

### Option B: From the CLI
```bash
cd cli
pip install .
threat-cli list
threat-cli run "Suspicious PowerShell"
```

Both paths trigger the same backend workflow.

---

## 6. Verify Telemetry

1. Return to the UI and open **Observability**. You should see a new hunt entry and alert.
2. (Optional) Launch `http://localhost:8000/docs` and call `/api/telemetry/events` to inspect raw JSON results.
3. Note the `matched_count`, `confidence`, and any alert routes that fired (Slack/Teams/PagerDuty/email if configured).

> 📸 Take screenshots of the Observability dashboard and Swagger response for documentation.

---

## 7. Clean Up

Stop the stack when you are done:

```bash
docker compose down
```

Add `-v` to remove persistent volumes if you want a fresh database on the next run.

---

## Next Steps

- Try the Linux and cloud hunts in [`docs/playbooks/`](../playbooks/).
- Create your own sample dataset and rule, then add a new playbook through the UI.
- Share feedback or questions on the project’s GitHub Discussions board.
