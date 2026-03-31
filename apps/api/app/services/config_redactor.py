import re


REDACTION_PATTERNS = [
    re.compile(r"^(username\s+\S+\s+(?:password|secret)\s+)\S+.*$", re.IGNORECASE),
    re.compile(r"^(enable\s+secret\s+)\S+.*$", re.IGNORECASE),
    re.compile(r"^(snmp-server\s+community\s+)\S+.*$", re.IGNORECASE),
    re.compile(r"^(tacacs-server\s+key\s+)\S+.*$", re.IGNORECASE),
    re.compile(r"^(radius-server\s+key\s+)\S+.*$", re.IGNORECASE),
    re.compile(r"^(key\s+\S+\s+)\S+.*$", re.IGNORECASE),
    re.compile(r"^((?:ip\s+ssh\s+pubkey-chain.*|crypto\s+isakmp\s+key\s+))\S+.*$", re.IGNORECASE),
]


INLINE_PASSWORD_PATTERN = re.compile(r"(\bpassword\s+)\S+", re.IGNORECASE)


def redact_config(config_text: str) -> str:
    redacted_lines: list[str] = []
    for line in config_text.splitlines():
        new_line = line
        for pattern in REDACTION_PATTERNS:
            match = pattern.match(new_line.strip())
            if match:
                prefix = match.group(1)
                indent = new_line[: len(new_line) - len(new_line.lstrip())]
                new_line = f"{indent}{prefix}<redacted>"
                break
        else:
            new_line = INLINE_PASSWORD_PATTERN.sub(r"\1<redacted>", new_line)

        redacted_lines.append(new_line)

    suffix = "\n" if config_text.endswith("\n") else ""
    return "\n".join(redacted_lines) + suffix
