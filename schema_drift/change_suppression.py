"""Suppression rules for schema changes — allows known/expected changes to be muted."""
from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import List, Optional

from schema_drift.diff import DiffResult, SchemaChange, ChangeType


@dataclass
class SuppressionRule:
    """A rule that suppresses matching schema changes from reporting."""
    table_pattern: str = "*"
    column_pattern: str = "*"
    change_types: List[ChangeType] = field(default_factory=list)
    reason: str = ""

    def matches(self, change: SchemaChange) -> bool:
        """Return True if this rule suppresses the given change."""
        if not fnmatch(change.table_name, self.table_pattern):
            return False
        col = change.column_name or ""
        if not fnmatch(col, self.column_pattern):
            return False
        if self.change_types and change.change_type not in self.change_types:
            return False
        return True


@dataclass
class SuppressionResult:
    """Outcome of applying suppression rules to a diff."""
    original: DiffResult
    suppressed: List[SchemaChange] = field(default_factory=list)
    retained: List[SchemaChange] = field(default_factory=list)

    @property
    def suppression_count(self) -> int:
        return len(self.suppressed)

    @property
    def has_retained_changes(self) -> bool:
        return len(self.retained) > 0


def apply_suppressions(
    diff: DiffResult,
    rules: List[SuppressionRule],
) -> SuppressionResult:
    """Apply suppression rules to a diff, separating suppressed from retained changes."""
    suppressed: List[SchemaChange] = []
    retained: List[SchemaChange] = []

    for change in diff.changes:
        if any(rule.matches(change) for rule in rules):
            suppressed.append(change)
        else:
            retained.append(change)

    return SuppressionResult(
        original=diff,
        suppressed=suppressed,
        retained=retained,
    )


def suppression_summary(result: SuppressionResult) -> str:
    """Return a short human-readable summary of suppression activity."""
    total = len(result.original.changes)
    sup = result.suppression_count
    ret = len(result.retained)
    return (
        f"Suppression summary: {total} total change(s), "
        f"{sup} suppressed, {ret} retained."
    )
