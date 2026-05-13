"""Rollup: aggregate multiple DiffResults into a period summary."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from schema_drift.diff import DiffResult, ChangeType


@dataclass
class RollupEntry:
    from_version: str
    to_version: str
    captured_at: datetime
    total_changes: int
    added_columns: int
    removed_columns: int
    modified_columns: int
    added_tables: int
    removed_tables: int

    def to_dict(self) -> dict:
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "captured_at": self.captured_at.isoformat(),
            "total_changes": self.total_changes,
            "added_columns": self.added_columns,
            "removed_columns": self.removed_columns,
            "modified_columns": self.modified_columns,
            "added_tables": self.added_tables,
            "removed_tables": self.removed_tables,
        }


@dataclass
class RollupReport:
    period_start: datetime
    period_end: datetime
    entries: List[RollupEntry] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return sum(e.total_changes for e in self.entries)

    @property
    def most_active_version_pair(self) -> Optional[str]:
        if not self.entries:
            return None
        top = max(self.entries, key=lambda e: e.total_changes)
        return f"{top.from_version} -> {top.to_version}"

    def to_dict(self) -> dict:
        return {
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_changes": self.total_changes,
            "most_active_version_pair": self.most_active_version_pair,
            "entries": [e.to_dict() for e in self.entries],
        }


def _count_by_type(diff: DiffResult, change_type: ChangeType) -> int:
    return sum(1 for c in diff.changes if c.change_type == change_type)


def build_entry(diff: DiffResult) -> RollupEntry:
    """Convert a single DiffResult into a RollupEntry."""
    return RollupEntry(
        from_version=diff.from_version,
        to_version=diff.to_version,
        captured_at=datetime.utcnow(),
        total_changes=len(diff.changes),
        added_columns=_count_by_type(diff, ChangeType.COLUMN_ADDED),
        removed_columns=_count_by_type(diff, ChangeType.COLUMN_REMOVED),
        modified_columns=_count_by_type(diff, ChangeType.COLUMN_MODIFIED),
        added_tables=_count_by_type(diff, ChangeType.TABLE_ADDED),
        removed_tables=_count_by_type(diff, ChangeType.TABLE_REMOVED),
    )


def build_rollup(diffs: List[DiffResult], period_start: datetime, period_end: datetime) -> RollupReport:
    """Aggregate a list of DiffResults into a RollupReport."""
    entries = [build_entry(d) for d in diffs]
    return RollupReport(period_start=period_start, period_end=period_end, entries=entries)
