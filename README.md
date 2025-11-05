# Threat Hunting Playbooks

Threat Hunting Playbooks is an end-to-end hunting platform that operationalises Sigma and YARA detections, orchestrates scheduled investigations, and guides analysts through enrichment workflows. The stack combines a FastAPI backend, Celery worker, Next.js frontend, and CLI utilities to execute hunts across Splunk, Elastic, and Microsoft Sentinel data sources.

## Key Capabilities

- **Detection catalog** – Manage Sigma and YARA rules with validation tooling and reusable templates.
- **Run orchestration** – Execute hunts on demand or on a schedule through the REST API, Celery worker, and CLI.
- **Connector ecosystem** – Translate Sigma logic for Splunk, Elastic, and Sentinel targets with pluggable enrichment primitives.
- **Operational UI** – Monitor playbooks, configure schedules, review outcomes, and inspect telemetry through the React/Next.js dashboard.
- **Observability & alerting** – Stream hunt telemetry to Prometheus/Grafana, capture metrics/alerts, and integrate with downstream notification channels.
- **Artifact governance** – Store results, logs, and supporting assets in PostgreSQL, MinIO, and shared volumes for downstream analysis.

## Architecture

```
Frontend (Next.js)  ←→  FastAPI service  ←→  PostgreSQL
         │                │
         │                ├─ Celery worker (scheduled hunts)
         │                ├─ Splunk / Elastic / Sentinel connectors
         │                ├─ Redis (broker + cache)
         │                ├─ MinIO (artifact storage)
         │                └─ Prometheus + Grafana (metrics & dashboards)
CLI client ──────────────┘
```

Each component is containerised and orchestrated via Docker Compose for local development and evaluation.

## Repository Layout

```
Threat Hunting Playbooks/
├── api/                 # FastAPI application, Celery tasks, connectors, ORM models
├── cli/                 # Click-based CLI client for playbook and schedule management
├── config/              # Shared configuration files and data source mappings
├── docs/                # Project documentation and references
├── hunts/               # Narrative playbooks aligning detections with investigation steps
├── notebooks/
│   ├── enrichment/      # Ready-to-run enrichment notebooks
│   └── templates/       # Notebook blueprints for new workflows
├── rules/
│   ├── sigma/           # Sigma detections and templates
│   └── yara/            # YARA detections and templates
├── samples/             # Example event data for local execution
├── scripts/             # Linting and validation utilities (Sigma, YARA, notebooks)
├── ui/                  # Next.js application with React Query-driven UX
├── docker-compose.yml   # Local orchestration of the complete stack
└── requirements.txt     # Notebook/tooling dependencies for analysts
```

## Prerequisites

- Docker Engine ≥ 24 and Docker Compose ≥ 2.20
- Node.js 18+ and npm 9+ (one-time dependency install for the UI)
- Python 3.11+ (optional for running notebooks and tooling locally)

## Quick Start (Docker Compose)

```bash
git clone https://github.com/sr-857/threat-hunting-playbooks.git
cd threat-hunting-playbooks

# Install front-end dependencies once to satisfy TypeScript linting
cd ui && npm install && cd ..

# Bring up the full stack
docker compose up --build
```

Services exposed by default:

| Service | URL | Notes |
| --- | --- | --- |
| UI | `http://localhost:3000` | Schedule management dashboard and playbook catalog |
| API | `http://localhost:8000/api` | FastAPI endpoints (`/health`, `/playbooks`, `/schedules`, …) |
| Celery worker | Logs in container output | Executes scheduled hunts |
| PostgreSQL | `postgresql://threat_user:threat_pass@localhost:5432/threat_playbooks` | Persistent metadata |
| Redis | `redis://localhost:6379/0` | Celery broker and cache |
| MinIO console | `http://localhost:9001` (minioadmin/minioadmin) | Artifact/object storage |
| Prometheus | `http://localhost:9090` | Metrics scraping / alert rules |
| Grafana | `http://localhost:3001` (admin/admin) | Dashboards visualising hunt telemetry |

Stop the environment with `docker compose down`. Use `docker compose down -v` to remove persistent volumes if you want a clean slate.

## CLI Usage

The CLI streamlines interaction with the API and scheduler.

```bash
cd cli
pip install .          # Installs the `threat-cli` entry point

# List playbooks
threat-cli list --api-url http://localhost:8000

# Execute a playbook immediately
threat-cli run <playbook_id>

# Manage schedules (list, create, update, delete, run)
threat-cli schedules list
threat-cli schedules create --name "Daily Hunt" --playbook <id> --cron "0 * * * *"
```

Use `THREAT_API_URL` to set a default API base URL for all commands.

## Development Workflow

### Backend (FastAPI & Celery)

```bash
cd api
poetry install  # or pip install -r requirements if preferred
poetry run uvicorn app.main:app --reload
poetry run celery -A app.scheduler.celery_app.celery_app worker --loglevel=info
```

### Frontend (Next.js)

```bash
cd ui
npm install        # if not already executed
npm run dev        # http://localhost:3000
npm run lint       # optional TypeScript/ESLint checks
npm run build      # production build verification
```

### Validation Utilities

```bash
./scripts/validate_sigma.sh   # Lints and converts Sigma content
./scripts/validate_yara.sh    # Compiles YARA rules for syntax errors
```

## Configuration

Environment variables are managed in `docker-compose.yml`. Notable settings include:

| Variable | Description | Default |
| --- | --- | --- |
| `DATABASE_URL` | SQLAlchemy connection string | `postgresql+asyncpg://threat_user:threat_pass@db:5432/threat_playbooks` |
| `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY` | Object storage configuration | `http://minio:9000`, `minioadmin`, `minioadmin` |
| `REDIS_URL`, `CELERY_BROKER_URL` | Celery broker and cache | `redis://redis:6379/0` |
| `NEXT_PUBLIC_API_URL` | Frontend → API base URL | `http://api:8000` |
| `JSON_LOGS` | Output structured JSON logs instead of console format | `false` |
| `ENABLE_METRICS` | Toggle Prometheus metrics exposure | `true` |
| `METRICS_ENDPOINT` | FastAPI metrics endpoint path | `/metrics` |
| `METRICS_NAMESPACE` | Prometheus metric prefix | `threat_playbooks` |
| `WORKER_METRICS_PORT` | Celery worker Prometheus port | `9002` |
| `ALERT_CONFIDENCE_THRESHOLD` | Confidence ratio that raises an alert | `0.7` |
| `ALERT_WEBHOOK_URL` | Optional webhook for high-confidence alerts | `null` |

Adjust these values (for example via `.env` files) before deploying to shared environments. Harden credentials, enable TLS termination, and integrate external observability as needed.

## Deployment Considerations

- **Production readiness** – Add HTTPS, secrets management, and central logging. Provision managed PostgreSQL/Redis/MinIO services or equivalent cloud offerings.
- **Scaling** – Run multiple Celery workers to process concurrent schedules. Front the API and UI with a reverse proxy or load balancer.
- **Monitoring** – Scrape `/metrics` with Prometheus, visualise dashboards in Grafana, consume `/api/telemetry/{events,alerts}`, and integrate alert webhooks.
- **Backups** – Enable regular backups for PostgreSQL and MinIO buckets storing hunt artifacts.

## Observability & Alerting

- **Telemetry endpoints** – Access recent executions and priority alerts via `/api/telemetry/events` and `/api/telemetry/alerts`.
- **Prometheus metrics** – Hunt counters/gauges (`hunt_runs_total`, `hunt_alerts_total`, etc.) are exposed for dashboards and alerting rules.
- **Grafana dashboards** – The UI surfaces a built-in Observability view, while Grafana (port `3001`) can consume Prometheus (`http://prometheus:9090`) for richer analytics.
- **Alert thresholds** – Configure `ALERT_CONFIDENCE_THRESHOLD` (and optional `ALERT_WEBHOOK_URL`) to drive automated notifications.

## Contributing

1. Fork the repository and create a feature branch.
2. Run validation scripts for Sigma/YARA content before submitting pull requests.
3. Ensure new connectors or playbooks include documentation and ATT&CK mappings in `docs/` and `hunts/`.
4. Open a pull request describing the change, testing performed, and any follow-on tasks.

## License

License details will be published in `LICENSE`. Until then, contributions are accepted under the terms communicated by the project maintainers.
