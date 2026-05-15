"""Assigns ownership (team/owner) to schema changes based on configurable rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Optional

from schema_drift.diff import DiffResult, SchemaChange


@dataclass
class OwnershipRule:
    """Maps a table pattern (and optional column pattern) to an owner label."""
    owner: str
    table_pattern: str = "*"
    column_pattern: str = "*"

    def matches(self, change: SchemaChange) -> bool:
        table_ok = fnmatch(change.table, self.table_pattern)
        col = change.column or ""
        col_ok = fnmatch(col, self.column_pattern)
        return table_ok and col_ok


@dataclass
class OwnedChange:
    change: SchemaChange
    owner: str

    def to_dict(self) -> dict:
        return {
            "owner": self.owner,
            "table": self.change.table,
            "column": self.change.column,
            "change_type": self.change.change_type.value,
        }


@dataclass
class OwnershipReport:
    from_version: str
    to_version: str
    owned: List[OwnedChange] = field(default_factory=list)
    unowned: List[SchemaChange] = field(default_factory=list)

    def is_empty(self) -> bool:
        return not self.owned and not self.unowned

    def by_owner(self) -> dict[str, List[OwnedChange]]:
        result: dict[str, List[OwnedChange]] = {}
        for oc in self.owned:
            result.setdefault(oc.owner, []).append(oc)
        return result

    def to_dict(self) -> dict:
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "owned": [oc.to_dict() for oc in self.owned],
            "unowned": [
                {"table": c.table, "column": c.column, "change_type": c.change_type.value}
                for c in self.unowned
            ],
        }


def assign_ownership(
    diff: DiffResult,
    rules: List[OwnershipRule],
) -> OwnershipReport:
    """Assign ownership to each change in *diff* using the first matching rule."""
    report = OwnershipReport(
        from_version=diff.from_version,
        to_version=diff.to_version,
    )
    for change in diff.changes:
        matched: Optional[str] = None
        for rule in rules:
            if rule.matches(change):
                matched = rule.owner
                break
        if matched:
            report.owned.append(OwnedChange(change=change, owner=matched))
        else:
            report.unowned.append(change)
    return report
