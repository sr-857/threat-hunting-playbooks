# Demo Screenshot Checklist

Use this directory to store PNG or WebP assets captured during the one-command demo and analyst workflow walkthroughs. Suggested filenames:

| Workflow Moment | Filename | Capture Tips |
| --- | --- | --- |
| CLI demo summary | `demo-cli-summary.png` | Run `make demo` and screenshot the final terminal block with match counts and token. |
| Playbook match table | `playbook-detail-matches.png` | Open the SaaS Credential Stuffing playbook in the UI after the demo run and capture the match grid. |
| Observability dashboard | `observability-alert-tile.png` | Navigate to `/observability` and grab the hunt card showing the recent run and confidence. |
| Telemetry API response | `telemetry-events.png` | Use Swagger (`/docs`) to call `/api/telemetry/events` and clip the JSON response. |

When adding new screenshots:

1. Place the file in this folder with a descriptive, kebab-case filename.
2. Update the relevant documentation page to reference the image using a relative path, for example:
   ```markdown
   ![Observability alert tile](../assets/observability-alert-tile.png)
   ```
3. Ensure any sensitive data is masked or replaced with synthetic values before committing.
