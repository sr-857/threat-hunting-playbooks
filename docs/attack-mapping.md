# MITRE ATT&CK Coverage Matrix

This matrix captures the current hunt library’s alignment to MITRE ATT&CK tactics and techniques. Update the table whenever you add or retire hunts.

| Hunt | Tactic | Technique | Description |
| --- | --- | --- | --- |
| Windows Lateral Movement via WMI | TA0008 – Lateral Movement | T1047 – Windows Management Instrumentation | Detects remote WMI execution used for cross-host pivoting. |
| Windows Lateral Movement via WMI | TA0002 – Execution | T1021.006 – Remote Services: Windows Remote Management (WinRM) | Flags suspicious remote PowerShell / WMI command execution. |

## Usage Guidance

- **Gap analysis**: Filter by tactic to identify defensive blind spots. Prioritise hunts for gaps aligned to your threat model.
- **Reporting**: Reference this matrix in quarterly SOC reports to illustrate coverage improvements.
- **Automation**: Export as CSV/JSON if your governance tooling requires machine-readable mappings.

## Extending the Matrix

1. Duplicate rows for each new hunt and populate the tactic/technique columns.
2. Link to the hunt metadata file (e.g., `hunts/<category>/<hunt>.yml`) so analysts can jump straight to implementation details.
3. If a hunt covers multiple tactics/techniques, add additional rows to reflect each mapping.

Future enhancements may include a script to generate this document automatically from `hunt.yml` metadata once multiple hunts exist.
