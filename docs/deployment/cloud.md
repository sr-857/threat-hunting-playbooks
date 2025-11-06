# Cloud Deployment Reference

This guide provides baseline considerations for deploying the Threat Hunting Playbooks stack to public cloud environments (AWS, Azure, GCP). It assumes you are comfortable with container orchestration and basic DevOps tooling.

## Common Architecture Patterns

| Component | Responsibility | Cloud Options |
| --- | --- | --- |
| API & Worker | FastAPI + Celery containers | ECS/Fargate, EKS, AKS, GKE, Cloud Run (API only) |
| PostgreSQL | Hunt metadata persistence | Amazon RDS, Azure Database for PostgreSQL, Cloud SQL |
| Redis | Celery broker/cache | AWS ElastiCache, Azure Cache for Redis, Memorystore |
| MinIO | Artifact/object storage | S3-compatible storage (Amazon S3, Azure Blob, Google Cloud Storage) |
| Frontend | Next.js UI | Static hosting (S3+CloudFront, Azure Static Web Apps, Firebase Hosting) |
| Observability | Prometheus + Grafana | Managed Prometheus/Grafana, Amazon Managed Grafana, Azure Monitor, Google Cloud Managed Service for Prometheus |

## Deployment Steps

1. **Provision managed services**:
   - Create PostgreSQL, Redis, and object storage instances with appropriate networking and IAM policies.
   - Store secrets (DB passwords, JWT secret, admin credentials) in a secret manager (AWS Secrets Manager, Azure Key Vault, Google Secret Manager).

2. **Container builds**:
   - Use CI/CD to build versioned images from the `api/` and `ui/` directories.
   - Push images to a private registry (ECR, ACR, Artifact Registry). Tag builds with commit SHA or semantic versions.

3. **Infrastructure as Code**:
   - Define infrastructure using Terraform, Pulumi, or native templates (CloudFormation, ARM/Bicep, Deployment Manager).
   - Include security groups / network security groups to limit ingress to API/UI and internal services.

4. **Orchestrator configuration**:
   - For Kubernetes-based deployments, create separate Deployments for `api` and `worker`. Use Horizontal Pod Autoscalers to scale Celery workers based on queue depth.
   - Mount a persistent volume or object storage gateway for MinIO artifacts, or replace MinIO with a managed S3-compatible service and update configuration accordingly.

5. **Secrets & Config**:
   - Inject environment variables (database URLs, Redis URL, JWT secret) via orchestrator-secret mechanisms.
   - Configure `INITIAL_ADMIN_EMAIL`/`INITIAL_ADMIN_PASSWORD` for bootstrap. After first login, rotate the password and store it securely.

6. **Networking**:
   - Expose the API behind an API gateway or application load balancer with TLS termination.
   - Restrict worker and database components to private subnets; expose UI/API through public endpoints only if necessary.

7. **Observability**:
   - Forward logs to a managed logging service (CloudWatch Logs, Azure Monitor Logs, Cloud Logging).
   - Scrape Prometheus metrics (or export to a managed solution); provision Grafana dashboards for hunt telemetry.

8. **Security**:
   - Enable role-based access control using the authentication features added to the API.
   - Integrate managed identity providers (AWS IAM, Azure AD, Google IAM) for service-to-service authentication where possible.
   - Configure WAF rules to protect the public API/UI endpoints.

9. **Disaster Recovery**:
   - Schedule automated backups for PostgreSQL and object storage.
   - Define infrastructure state in IaC for rapid re-deployment.

## Scaling Considerations

- **Celery workers**: Scale using queue metrics; consider auto-scaling policies that react to hunt frequency and duration.
- **Database**: Monitor CPU/IO; upgrade compute tiers or enable read replicas if query load grows.
- **UI/API**: Use load balancing with health checks to ensure rolling updates don’t disrupt analysts.

## CI/CD Integration

- Use GitHub Actions, GitLab CI, or your provider’s pipelines to build and push container images on every merge.
- Run tests (unit, API, UI) as part of the pipeline before promoting builds to staging/production clusters.
- Gate production deployments behind manual approvals or change management workflows.

## Compliance & Governance

- Ensure hunt telemetry stored in object storage complies with data residency requirements.
- Audit API access logs for analyst actions; integrate with SIEM solutions for long-term retention.
- Document RBAC policies, alert thresholds, and escalation paths as part of your SOC runbooks.

This reference outlines the high-level path. Tailor the specifics to your organisation’s cloud platform, security controls, and capacity requirements.
