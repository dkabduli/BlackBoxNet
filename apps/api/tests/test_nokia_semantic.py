from app.core.semantic_extraction.nokia_sros import NokiaSROSExtractor


def test_detects_static_label_collision() -> None:
    old = "fec-originate 10.0.1.0/24\n"
    new = old + "fec-originate 10.0.5.0/24\n    static-label-map 131071\n"
    diff = "--- a\n+++ b\n+static-label-map 131071\n"
    changes = NokiaSROSExtractor().extract_changes(diff, old, new)
    assert any(c.change_type == "LDP_LABEL_COLLISION" for c in changes)
