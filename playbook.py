from schema import LogEvent

REMEDIATIONS: dict[str, str] = {
    "out of memory": "Increase heap/memory allocation or investigate a memory leak; restart the affected service.",
    "connection refused": "Verify the target service is running and listening on the expected port; check firewall and network routes.",
    "timeout": "Increase the timeout threshold if appropriate and investigate downstream latency or resource contention.",
    "disk full": "Free disk space or expand the volume; rotate and archive old logs.",
    "permission denied": "Check file/resource ownership and permissions; verify the running user has required access.",
    "null pointer": "Add a null/None check at the failing call site and validate upstream inputs.",
    "authentication failure": "Verify credentials and auth configuration; check for expired tokens or keys.",
}


def apply_playbook(event: LogEvent) -> LogEvent:
    try:
        haystack = event.suggested_remediation.lower()
        for keyword, remediation in REMEDIATIONS.items():
            if keyword in haystack:
                event.suggested_remediation = remediation
                return event
    except Exception:
        return event
    return event
