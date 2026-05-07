"""Filter schema changes by table name, column name, or change type."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Set

from schema_drift.diff import ChangeType, DiffResult, SchemaChange


@dataclass
class DiffFilter:
    """Criteria for filtering a DiffResult down to a subset of changes."""

    tables: Optional[List[str]] = None          # include only these tables (None = all)
    change_types: Optional[List[ChangeType]] = None  # include only these types (None = all)
    exclude_tables: List[str] = field(default_factory=list)

    def matches(self, change: SchemaChange) -> bool:
        """Return True if *change* satisfies every active criterion."""
        if self.tables is not None:
            if change.table not in self.tables:
                return False

        if change.table in self.exclude_tables:
            return False

        if self.change_types is not None:
            if change.change_type not in self.change_types:
                return False

        return True


def apply_filter(diff: DiffResult, diff_filter: DiffFilter) -> DiffResult:
    """Return a new DiffResult containing only changes that match *diff_filter*."""
    filtered_changes: List[SchemaChange] = [
        c for c in diff.changes if diff_filter.matches(c)
    ]
    return DiffResult(
        from_version=diff.from_version,
        to_version=diff.to_version,
        changes=filtered_changes,
    )


def unique_tables(diff: DiffResult) -> Set[str]:
    """Return the set of table names referenced in *diff*."""
    return {c.table for c in diff.changes}


def changes_by_table(diff: DiffResult) -> dict:
    """Return a mapping of table name -> list of SchemaChange."""
    result: dict = {}
    for change in diff.changes:
        result.setdefault(change.table, []).append(change)
    return result
