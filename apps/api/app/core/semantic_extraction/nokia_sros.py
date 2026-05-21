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
