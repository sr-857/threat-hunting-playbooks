# Analyst Workflow Guide

Speed and clarity are critical for SOC analysts. This guide maps common workflows to the Threat Hunting Playbooks UI and CLI so teams can move from detection to response quickly.

## 1. Daily Hunt Review
1. Open the dashboard at `http://localhost:3000/observability`.
2. Filter by **Recent Hunts** to display the last 24 hours.
3. Use the **Confidence** sorting to prioritise investigations.
4. For each hunt, click **View Details** → **Pivot Actions** to launch enrichment notebooks or connector reruns.

### Tips
- Bookmark the Observability dashboard for one-click morning reviews.
- Export the run summary via the **Download JSON** action for handoff to IR teams.

## 2. Alert Triage & Pivot
1. From an alert card, select **Related Telemetry** to view raw events.
2. Use quick pivots:
   - **Open in Notebook** – launches the referenced enrichment notebook (Jupyter).
   - **Replay in Connector** – re-issues the query with adjusted time range.
   - **Export to CSV** – prepares data for case management import.
3. Update the status (New → In Progress → Closed) to maintain SOC queue hygiene.

### UX Enhancements in Progress
- Bulk status edits for batched alert closure.
- Inline link-outs to case management platforms (ServiceNow, JIRA).

## 3. Playbook Authoring
1. Navigate to **Playbooks → Add Playbook**.
2. Provide metadata and attach Sigma/YARA rules plus sample datasets.
3. Test-run via **Run Now**, then schedule via the CLI for recurring coverage.
4. Document tuning notes directly in the playbook markdown under `docs/playbooks/`.

### Recommended Practices
- Pair each new playbook with a JSONL sample stored under `samples/logs/`.
- Capture screenshots of UI forms to include in documentation (see `docs/playbooks/examples.md`).

## 4. Collaboration & Handoff
- Use the **Notes** tab on playbooks to log assumptions and follow-up work.
- Create GitHub issues directly from the UI (roadmap feature) or via templates in `.github/ISSUE_TEMPLATE/`.
- Announce significant hunts or findings in the `[Discussions](https://github.com/sr-857/threat-hunting-playbooks/discussions)` board.

## 5. Pending UX Improvements
| Area | Current State | Planned Improvement |
| --- | --- | --- |
| Empty States | Text-only prompts | Add quick-start buttons (Run demo hunt, Upload sample data) |
| Navigation | Flat menu | Grouped sections (Playbooks, Telemetry, Automation) |
| Alert Timeline | Static table | Interactive timeline with hover details |
| Pivot Shortcuts | Manual tabs | One-click buttons for common pivots (GeoIP, Threat Intel) |

## Feedback Loop
- File usability issues under `UI / UX` label in GitHub Issues.
- Share workflow diagrams in `docs/ux/`—pull requests welcome.
- Join the monthly community call (details in README badges) to vote on UX roadmap items.
