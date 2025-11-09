# Getting Started

Welcome to the Threat Hunting Playbooks platform. This guide walks new analysts and operators through local setup, account provisioning, and first-run validation.

## Prerequisites

- **Operating system**: Linux or macOS (Windows users should run inside WSL2)
- **Containers**: Docker Engine ≥ 24 and Docker Compose ≥ 2.20
- **Node.js tooling**: Node.js 18+ and npm 9+ (needed once for the UI build)
- **Python**: 3.11+ with Poetry or virtualenv tooling for optional CLI/local utilities

Optional dependencies:

- `make`, `jq`, and `yq` for scripting convenience
- `kubectl` and `helm` if you plan to deploy to Kubernetes later

## Clone the Repository

```bash
git clone https://github.com/sr-857/threat-hunting-playbooks.git
cd threat-hunting-playbooks
```

If you forked the repository, update the origin remote accordingly.

## Install Frontend Dependencies

One-time installation ensures TypeScript linting and builds succeed locally.

```bash
cd ui
npm install
cd ..
```

> **Tip:** The `/ui/node_modules` directory is ignored by Git to avoid large commits.

## Configure Environment Variables

Default settings are baked into `docker-compose.yml`, but you can override them by creating an `.env` file in the project root. Common overrides:

```env
POSTGRES_PASSWORD=your-strong-password
SECRET_KEY=long-random-string
INITIAL_ADMIN_EMAIL=admin@example.com
INITIAL_ADMIN_PASSWORD=ChangeMeNow!
MINIO_ENABLED=true
MINIO_PRESIGN_TTL_SECONDS=900
```

`MINIO_ENABLED` toggles artifact uploads to the MinIO bucket, while `MINIO_PRESIGN_TTL_SECONDS` controls how long generated download links remain valid. The API reads these values via `app/core/config.py`. For production, use a secrets manager or orchestrator-level secret injection.

## Launch the Stack with Docker Compose

```bash
docker compose up --build
```

Services exposed after a successful launch:

| Service | URL | Description |
| --- | --- | --- |
| UI | `http://localhost:3000` | Analyst dashboard and hunt catalog |
| API | `http://localhost:8000/api` | FastAPI endpoints secured with JWT |
| Docs (Swagger) | `http://localhost:8000/docs` | Interactive API documentation |
| Prometheus | `http://localhost:9090` | Metrics scraping |
| Grafana | `http://localhost:3001` | Observability dashboards |
| MinIO Console | `http://localhost:9001` | Artifact/object storage |

Stop the stack with `docker compose down`. Add `-v` to remove persistent volumes.

## Authenticate as the Initial Admin

During bootstrap the API seeds an administrator using the credentials configured by `INITIAL_ADMIN_EMAIL` / `INITIAL_ADMIN_PASSWORD` (defaults: `admin@example.com` / `ChangeMe123!`).

1. Request a token:
   ```bash
   curl -X POST http://localhost:8000/api/auth/token \
     -H 'Content-Type: application/x-www-form-urlencoded' \
     -d 'username=admin@example.com&password=ChangeMe123!'
   ```
2. Store the returned access token and include it in subsequent API/CLI calls via the `Authorization: Bearer <token>` header or `THREAT_API_TOKEN` environment variable.

Create additional users via the upcoming user-management endpoints or directly in the database for now.

## Run Your First Hunt

Use the CLI for a quick validation that the worker executes playbooks end-to-end:

```bash
cd cli
pip install .
THREAT_API_URL=http://localhost:8000 THREAT_API_TOKEN="<token>" \
  threat-cli list
```

Trigger an on-demand hunt:

```bash
THREAT_API_URL=http://localhost:8000 THREAT_API_TOKEN="<token>" \
  threat-cli run <playbook-id>
```

Sigma rules are validated before execution—invalid or incomplete definitions will be rejected with actionable error messages. Review results in the UI under **Playbooks → Quick Run history** or via the telemetry endpoints powering the Observability dashboard.

## One-command Demo

Prefer a scripted tour you can run during onboarding sessions or executive demos? The repo ships with a `make demo` target that:

1. Builds and launches the full Docker Compose stack.
2. Polls the API until it is healthy.
3. Authenticates with the seeded administrator credentials.
4. Executes the **SaaS Credential Stuffing Campaign** playbook end-to-end.
5. Captures run output plus recent telemetry into `.demo-output/` for easy sharing.

```bash
make demo
# tear everything down afterwards
make demo-clean
```

When the script finishes it prints:

- Matched versus total records, confidence score, and execution notes.
- Paths to JSON artifacts (`*_run.json`, `telemetry_events.json`, `telemetry_alerts.json`).
- A fresh bearer token you can paste into the UI or CLI.

> **Screenshot checklist:** Capture the CLI summary, the Observability dashboard tile for the run, and the playbook detail view showing matched records. Save images under `docs/assets/` and reference them from documentation using relative paths (see [Example Hunts](./playbooks/examples.md#capturing-screenshots-for-documentation)).

## Next Steps

- Explore the [playbook walkthroughs](./playbooks/windows-lateral-movement.md) to understand metadata, enrichment, and analyst flow.
- Browse ready-to-run [example hunts](./playbooks/examples.md) for demo scripts and screenshot guidance.
- Map coverage to your threat landscape using the [ATT&CK coverage matrix](./attack-mapping.md).
- Plan a deployment on cloud infrastructure with the [cloud reference guide](./deployment/cloud.md).

With the stack up and authenticated, you are ready to tailor hunts, add new telemetry connectors, and integrate with SOC tooling.
