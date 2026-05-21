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


class JunosExtractor:
    def extract_changes(
        self, diff_text: str, old_config: str, new_config: str
    ) -> list[SemanticChange]:
        changes: list[SemanticChange] = []
        hold_re = re.compile(r"hold-time\s+(\d+)", re.M)
        old_holds = hold_re.findall(old_config)
        new_holds = hold_re.findall(new_config)
        if new_holds and (not old_holds or new_holds != old_holds):
            changes.append(
                SemanticChange(
                    change_type="JUNOS_BGP_HOLD_MISMATCH",
                    entity="bgp-group-upstream",
                    action="modified",
                    suspicion_level="critical",
                    reason="BGP hold-time change may desynchronize with upstream peer",
                    details={
                        "old_hold_time": old_holds[-1] if old_holds else None,
                        "new_hold_time": new_holds[-1],
                        "recommended_hold_time": "90",
                    },
                )
            )
        return changes
