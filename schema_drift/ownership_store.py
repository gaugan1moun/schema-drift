"""Persist and load OwnershipRule lists from a JSON config file."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List

from schema_drift.change_ownership import OwnershipRule


def _rule_to_dict(rule: OwnershipRule) -> dict:
    return {
        "owner": rule.owner,
        "table_pattern": rule.table_pattern,
        "column_pattern": rule.column_pattern,
    }


def _rule_from_dict(d: dict) -> OwnershipRule:
    return OwnershipRule(
        owner=d["owner"],
        table_pattern=d.get("table_pattern", "*"),
        column_pattern=d.get("column_pattern", "*"),
    )


class OwnershipStore:
    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def save(self, rules: List[OwnershipRule]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = [_rule_to_dict(r) for r in rules]
        self._path.write_text(json.dumps(data, indent=2))

    def load(self) -> List[OwnershipRule]:
        if not self._path.exists():
            raise FileNotFoundError(f"Ownership config not found: {self._path}")
        data = json.loads(self._path.read_text())
        return [_rule_from_dict(d) for d in data]

    def exists(self) -> bool:
        return self._path.exists()
