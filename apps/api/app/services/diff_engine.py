import difflib
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.semantic_extraction.cisco_ios import CiscoIOSExtractor, SemanticChange as CiscoChange
from app.core.semantic_extraction.nokia_sros import NokiaSROSExtractor, SemanticChange as NokiaChange
from app.core.semantic_extraction.junos import JunosExtractor, SemanticChange as JunosChange
from app.models.config import ConfigDiff, ConfigVersion


class DiffEngine:
    def __init__(self, db: AsyncSession):
        self._db = db
        self._cisco = CiscoIOSExtractor()
        self._nokia = NokiaSROSExtractor()
        self._junos = JunosExtractor()

    async def generate_diff(
        self,
        old_config: str,
        new_config: str,
        device_id: uuid.UUID,
        timestamp: datetime,
        previous_version: ConfigVersion | None,
        current_version: ConfigVersion,
        scenario_id: str,
        vendor: str = "cisco-ios",
    ) -> ConfigDiff:
        old_lines = old_config.splitlines(keepends=True)
        new_lines = new_config.splitlines(keepends=True)

        diff_lines = list(
            difflib.unified_diff(old_lines, new_lines, fromfile="previous", tofile="current")
        )
        diff_text = "".join(diff_lines)

        lines_added = sum(1 for l in diff_lines if l.startswith("+") and not l.startswith("+++"))
        lines_removed = sum(1 for l in diff_lines if l.startswith("-") and not l.startswith("---"))
        lines_changed = lines_added + lines_removed

        if vendor == "nokia-sros":
            semantic_changes: list[CiscoChange | NokiaChange | JunosChange] = self._nokia.extract_changes(
                diff_text, old_config, new_config
            )
        elif vendor == "junos":
            semantic_changes = self._junos.extract_changes(diff_text, old_config, new_config)
        else:
            semantic_changes = self._cisco.extract_changes(diff_text, old_config, new_config)
        max_suspicion = self._get_max_suspicion(semantic_changes)

        config_diff = ConfigDiff(
            scenario_id=scenario_id,
            device_id=device_id,
            previous_config_version_id=previous_version.id if previous_version else None,
            current_config_version_id=current_version.id,
            timestamp=timestamp,
            diff_text=diff_text,
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_changed=lines_changed,
            semantic_summary=[sc.to_dict() for sc in semantic_changes],
            suspicion_level=max_suspicion,
        )

        self._db.add(config_diff)
        await self._db.flush()
        return config_diff

    def _get_max_suspicion(self, changes: list[CiscoChange | NokiaChange]) -> str:
        levels = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        if not changes:
            return "low"
        max_level = max(levels.get(c.suspicion_level, 0) for c in changes)
        return {v: k for k, v in levels.items()}[max_level]
