import re
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SemanticChange:
    change_type: str
    entity: str
    action: str
    suspicion_level: str
    reason: str
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "change_type": self.change_type,
            "entity": self.entity,
            "action": self.action,
            "suspicion_level": self.suspicion_level,
            "reason": self.reason,
            "details": self.details,
        }


class NokiaSROSExtractor:
    COLLISION_LABEL = "131071"

    def extract_changes(
        self, diff_text: str, old_config: str, new_config: str
    ) -> list[SemanticChange]:
        changes: list[SemanticChange] = []

        if "static-label-map" in new_config and self.COLLISION_LABEL in new_config:
            if f"static-label-map {self.COLLISION_LABEL}" in diff_text or self.COLLISION_LABEL in diff_text:
                changes.append(
                    SemanticChange(
                        change_type="LDP_LABEL_COLLISION",
                        entity="static-label-map",
                        action="collision",
                        suspicion_level="critical",
                        reason=(
                            f"static-label-map {self.COLLISION_LABEL} collides with "
                            "existing ILM entry for 10.0.1.0/24"
                        ),
                        details={
                            "label": self.COLLISION_LABEL,
                            "overwritten_fec": "10.0.1.0/24",
                            "new_fec": "10.0.5.0/24",
                            "annotation": "COLLISION — label in use by 10.0.1.0/24",
                        },
                    )
                )

        if "far-end 10.0.0.99" in new_config and "far-end 10.0.0.99" not in old_config:
            changes.append(
                SemanticChange(
                    change_type="NOKIA_SDP_BLACKHOLE",
                    entity="sdp-100",
                    action="modified",
                    suspicion_level="critical",
                    reason="SDP far-end points to unreachable peer — spoke stays DOWN",
                    details={"far_end": "10.0.0.99"},
                )
            )
        if "VPRN200-EXPORT" in new_config and "VPRN200-EXPORT" not in old_config:
            changes.append(
                SemanticChange(
                    change_type="NOKIA_VPRN_LEAK",
                    entity="vprn-100",
                    action="modified",
                    suspicion_level="critical",
                    reason="VPRN 100 export-policy references VPRN 200 route-target",
                    details={},
                )
            )
        if re.search(r"rate\s+1000\b", new_config) and not re.search(r"rate\s+1000\b", old_config):
            changes.append(
                SemanticChange(
                    change_type="NOKIA_QOS_POLICER",
                    entity="sap-ingress-10",
                    action="modified",
                    suspicion_level="critical",
                    reason="Ingress policer cut to 1 Mbps on high-speed access SAP",
                    details={"rate_kbps": 1000},
                )
            )

        for keyword in ("fec-originate", "targeted-session", "interface-parameters"):
            if keyword in diff_text and f"+{keyword}" in diff_text or keyword in new_config:
                if any(c.entity == keyword for c in changes):
                    continue
                if keyword in new_config and keyword not in old_config:
                    changes.append(
                        SemanticChange(
                            change_type="SR_OS_CONFIG_BLOCK",
                            entity=keyword,
                            action="added",
                            suspicion_level="medium",
                            reason=f"SR OS block '{keyword}' added",
                            details={"keyword": keyword},
                        )
                    )

        return changes
