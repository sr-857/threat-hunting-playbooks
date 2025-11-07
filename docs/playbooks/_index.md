# Playbook Gallery

Ready-to-run hunts with sample data and walkthroughs. Use these to demo the platform or as templates for production hunts.

| Playbook | Platform | Description |
| --- | --- | --- |
| [Suspicious PowerShell](./windows-lateral-movement.md) | Windows | Detects encoded PowerShell execution used for lateral movement. |
| [Windows RDP Brute Force](./windows-rdp-bruteforce.md) | Windows | Flags rapid RDP failures followed by success, using sample security logs. |
| [Linux Cron Persistence](./linux-persistence.md) | Linux | Identifies malicious cron jobs executing payloads from `/tmp`. |
| [Cloud IAM Impossible Travel](./cloud-iam-anomalies.md) | Cloud | Surfaces abnormal sign-ins with the ImpossibleTravel risk. |
| [SaaS Credential Stuffing Campaign](./saas-credential-stuffing.md) | SaaS | Highlights distributed login failures followed by a suspicious success and MFA bypass. |
| [Linux SUID Dropper PrivEsc](./linux-suid-dropper.md) | Linux | Detects creation and execution of rogue SUID binaries for privilege escalation. |
| [Sentinel Connector Abuse](./sentinel-connector-abuse.md) | Azure | Monitors bulk connector changes and automation disablement in Microsoft Sentinel. |

> Need more examples? Contributions welcome—follow the guidance in `CONTRIBUTING.md`.
