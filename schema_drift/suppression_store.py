"""Persistence layer for suppression rules."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from schema_drift.change_suppression import SuppressionRule
from schema_drift.diff import ChangeType


def _rule_to_dict(rule: SuppressionRule) -> dict:
    return {
        "table_pattern": rule.table_pattern,
        "column_pattern": rule.column_pattern,
        "change_types": [ct.value for ct in rule.change_types],
        "reason": rule.reason,
    }


def _rule_from_dict(data: dict) -> SuppressionRule:
    return SuppressionRule(
        table_pattern=data.get("table_pattern", "*"),
        column_pattern=data.get("column_pattern", "*"),
        change_types=[
            ChangeType(ct) for ct in data.get("change_types", [])
        ],
        reason=data.get("reason", ""),
    )


class SuppressionStore:
    """Load and save suppression rules to a JSON file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def save(self, rules: List[SuppressionRule]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = [_rule_to_dict(r) for r in rules]
        self._path.write_text(json.dumps(payload, indent=2))

    def load(self) -> List[SuppressionRule]:
        if not self._path.exists():
            raise FileNotFoundError(
                f"Suppression rules file not found: {self._path}"
            )
        data = json.loads(self._path.read_text())
        return [_rule_from_dict(d) for d in data]

    def exists(self) -> bool:
        return self._path.exists()
