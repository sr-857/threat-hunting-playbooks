# Scaling Threat Hunting Playbooks

This guide outlines strategies for operating the platform against high-volume telemetry (200+ GB/day) across distributed collectors.

## 1. Reference Architecture
- **Control Plane:** API, UI, Celery worker, and scheduler deployed on Kubernetes (three replicas each) behind an ingress controller.
- **Data Plane:**
  - Kafka or Pulsar topic receives normalized telemetry from collectors.
  - Object storage (S3 or MinIO Gateway) retains hunt artifacts and sample datasets.
  - Managed databases (PostgreSQL, Redis) scaled with read replicas and high-availability configuration.
- **Connectors:** Run as sidecar deployments close to their data sources (e.g., Splunk Heavy Forwarders, Elastic Coordinating Nodes).

![Scale Architecture](../assets/scale-architecture.png)

## 2. Distributed Collectors
- Instrument log shippers (Fluent Bit, Winlogbeat, Cloud-native exporters) to publish to regional queues.
- Configure the CLI or scheduler to target regional connectors to avoid cross-region latency.
- Use Terraform modules in `deploy/terraform/` (coming soon) to provision collectors with secret injection.

## 3. Hunt Execution Strategy
| Component | Recommendation |
| --- | --- |
| Scheduler | Deploy multiple Celery beat instances with leader election (e.g., `redbeat`) |
| Worker Autoscaling | Use KEDA to scale Celery workers based on queue length / execution duration |
| Batching | Split large hunts into shard-specific jobs (per region / per index prefix) |
| Telemetry Storage | Route hunt results to time-series database (ClickHouse or Elasticsearch) with retention policies |

## 4. Data Handling Best Practices
- **Sampling:** For exploratory hunts, run on sampled subsets (1–5%) before expanding to full datasets.
- **Compression:** Store JSONL artifacts compressed (gzip) to reduce storage costs.
- **Retention:** Configure lifecycle policies (e.g., S3 Glacier) for hunt outputs older than 90 days.

## 5. Security & Compliance
- Rotate connector credentials using managed identity or workload identity.
- Store secrets in Kubernetes Secrets or a vault (HashiCorp Vault, AWS Secrets Manager).
- Enable TLS between workers and connectors; enforce mTLS for on-prem Splunk/Elastic endpoints.
- Audit scheduling changes via GitOps (pull requests updating cron definitions).

## 6. Monitoring & Observability
- Scrape worker metrics (execution duration, failure rate) via Prometheus; create Grafana dashboards per connector.
- Emit structured logs to central log store; tag by playbook ID and region.
- Configure alerts for:
  - Hunt execution duration SLA breaches.
  - Connector error rate spikes.
  - Telemetry ingestion backlog (Kafka lag, queue depth).

## 7. Disaster Recovery
- Maintain standby workers in a secondary region.
- Replicate object storage buckets and PostgreSQL database.
- Document runbook for rehydrating hunts from Git history and redeploying connectors.

## 8. Next Steps
- Automate infrastructure deployment via `deploy/terraform/` blueprints (planned).
- Publish Helm charts with horizontal pod autoscaler defaults.
- Capture customer case studies demonstrating scale-out patterns.
