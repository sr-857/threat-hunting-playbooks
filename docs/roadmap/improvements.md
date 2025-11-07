# Roadmap: Upcoming Enhancements

This document captures the next wave of improvements requested for Threat Hunting Playbooks. Each section outlines objectives, proposed approach, dependencies, and suggested deliverables.

---

## 1. Connector Testing Strategy

**Objective:** Increase confidence that Sigma rules translate correctly across Splunk, Elastic, and Microsoft Sentinel connectors.

**Approach:**
- Add unit tests validating translation output for representative Sigma detection blocks.
- Introduce pytest-based integration shims that exercise the async connector interface with mocked API responses.
- Run the connector test suite as part of the existing `api-tests` GitHub Action.

**Deliverables:**
- `tests/connectors/` suite (baseline added).
- CI updates ensuring translation regressions are caught.
- Developer guide snippet on writing new connector tests.

---

## 2. Advanced Scheduling Features

**Objective:** Support dependencies between hunts and adaptive scheduling triggered by intelligence signals.

**Approach:**
- Extend the scheduling model to store parent → child relationships and runtime conditions.
- Implement Celery orchestration that evaluates hunt outcomes and queues dependents when criteria are met (e.g., `matched_count > 0`).
- Ingest priority signals (from threat intel feeds or manual overrides) to temporarily adjust cron cadence.

**Deliverables:**
- Design ADR describing data model changes, Celery workflow, and UI/CLI updates.
- API endpoints to manage dependencies and priority rules.
- Documentation for operators on chaining hunts and tuning adaptive policies.

**Dependencies:** Threat intelligence ingestion (Section 5) can supply priority signals.

---

## 3. Connector Ecosystem Expansion

**Objective:** Broaden coverage beyond Splunk, Elastic, and Sentinel.

**Approach:**
- Define a `BaseConnector` helper for REST-based backends with templated query execution.
- Implement connectors for:
  - **Google Chronicle** – leverage Chronicle APIs for querying detection logs.
  - **Splunk SOAR / Phantom** – reuse Splunk authentication, expose playbook trigger endpoints.
  - **Generic REST** – allow teams to plug in custom APIs with minimal code.
- Provide scaffolding (sample configs, unit tests, docs) to encourage community contributions.

**Deliverables:**
- New connector modules with translation stubs and tests.
- Documentation under `docs/connectors/` describing configuration and sample hunts.
- Issue templates inviting external submissions for additional data sources.

---

## 4. Performance Optimization Guidance

**Objective:** Help teams scale the platform for large environments.

**Approach:**
- Document worker sizing, Redis tuning, queue configuration, and database/indexing best practices.
- Capture recommended Prometheus metrics and Grafana dashboards for monitoring hunt throughput.
- Outline steps for Kubernetes or autoscaling deployments.

**Deliverables:**
- `docs/deployment/performance.md` with checklists and tuning recipes.
- Example Grafana dashboard JSON and Prometheus alert rules (optional follow-up).

---

## 5. Threat Intelligence Integration

**Objective:** Dynamically adjust hunt priorities based on current threat landscape.

**Approach:**
- Add ingestion pipeline that normalizes STIX/TAXII feeds or JSON intel data into a local table.
- Map indicators to hunts via tags/techniques to elevate or suppress schedules.
- Expose configuration via API/CLI, with audit logging for changes.

**Deliverables:**
- Feed ingestion service or Celery task.
- Database models and APIs to manage indicator ↔ hunt relationships.
- Documentation explaining how to connect to external feeds and measure impact.

---

## Immediate Action Items

1. Finalize connector translation tests and integrate them into CI (in progress).
2. Draft ADRs/design docs for Sections 2 & 5 to align on data model changes before implementation.
3. Create GitHub issues for each major deliverable, tagged with appropriate labels (`help wanted`, `good first issue` for bite-sized tasks).
4. Schedule milestone releases (e.g., v0.6 “Connector Hardening”, v0.7 “Adaptive Scheduling”).

These enhancements will continue to mature the platform and align it with production-grade threat hunting requirements.
