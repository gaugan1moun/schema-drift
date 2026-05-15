"""Assigns blame (ownership) to schema changes based on table/column patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional

from schema_drift.diff import DiffResult, SchemaChange


@dataclass
class BlameRule:
    """Maps a table pattern to an owner label."""
    table_pattern: str
    owner: str

    def matches(self, table: str) -> bool:
        return fnmatch(table, self.table_pattern)


@dataclass
class BlamedChange:
    change: SchemaChange
    owner: Optional[str]

    def to_dict(self) -> dict:
        return {
            "table": self.change.table,
            "change_type": self.change.change_type.value,
            "column": self.change.column,
            "owner": self.owner,
        }


@dataclass
class BlameReport:
    from_version: str
    to_version: str
    blamed: List[BlamedChange] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.blamed) == 0

    def by_owner(self) -> Dict[str, List[BlamedChange]]:
        result: Dict[str, List[BlamedChange]] = {}
        for bc in self.blamed:
            key = bc.owner or "unowned"
            result.setdefault(key, []).append(bc)
        return result

    def to_dict(self) -> dict:
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "blamed": [b.to_dict() for b in self.blamed],
        }


def _resolve_owner(table: str, rules: List[BlameRule]) -> Optional[str]:
    for rule in rules:
        if rule.matches(table):
            return rule.owner
    return None


def build_blame_report(diff: DiffResult, rules: List[BlameRule]) -> BlameReport:
    """Produce a BlameReport by matching each change against the given rules."""
    blamed = [
        BlamedChange(
            change=change,
            owner=_resolve_owner(change.table, rules),
        )
        for change in diff.changes
    ]
    return BlameReport(
        from_version=diff.from_version,
        to_version=diff.to_version,
        blamed=blamed,
    )
