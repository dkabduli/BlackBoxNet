from app.services.config_redactor import redact_config


def test_redact_config_masks_common_secret_lines() -> None:
    original = """username admin secret supersecret
enable secret 5 $1$abcdef
snmp-server community public RO
line vty 0 4
 password cisco
"""

    redacted = redact_config(original)

    assert "supersecret" not in redacted
    assert "$1$abcdef" not in redacted
    assert "public RO" not in redacted
    assert "password cisco" not in redacted
    assert "<redacted>" in redacted
