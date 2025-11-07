rule Linux_SUID_Dropper
{
    meta:
        description = "Detects ELF binaries compiled in /tmp and marked SUID for privilege escalation"
        author = "Threat Hunting Playbooks Team"
        reference = "https://attack.mitre.org/techniques/T1548/001/"
    strings:
        $tmp_path = "/tmp/.cache/.sshd_helper"
        $suid_func = "setuid"
        $priv_escalation_cmd = "--check"
    condition:
        uint32(0) == 0x7f454c46 and (any of ($tmp_path, $priv_escalation_cmd) and $suid_func)
}
