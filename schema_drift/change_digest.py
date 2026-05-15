"""Periodic digest summarising schema changes across a time window."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Dict, List, Optional

from schema_drift.rollup import RollupEntry


@dataclass
class DigestEntry:
    period: str          # ISO date string (start of window)
    window_days: int
    total_changes: int
    tables_affected: int
    top_change_types: Dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "period": self.period,
            "window_days": self.window_days,
            "total_changes": self.total_changes,
            "tables_affected": self.tables_affected,
            "top_change_types": self.top_change_types,
        }


@dataclass
class ChangeDigest:
    entries: List[DigestEntry] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.entries) == 0

    def latest(self) -> Optional[DigestEntry]:
        return self.entries[-1] if self.entries else None

    def total_changes(self) -> int:
        return sum(e.total_changes for e in self.entries)

    def to_dict(self) -> dict:
        return {"entries": [e.to_dict() for e in self.entries]}


def build_digest(
    rollup_entries: List[RollupEntry],
    window_days: int = 7,
    reference_date: Optional[date] = None,
) -> ChangeDigest:
    """Group rollup entries into digest windows of *window_days* days."""
    if not rollup_entries:
        return ChangeDigest()

    ref = reference_date or date.today()
    window = timedelta(days=window_days)

    # Determine bucket boundaries (newest first)
    oldest = min(date.fromisoformat(e.from_version[:10]) for e in rollup_entries)
    buckets: List[date] = []
    cursor = ref
    while cursor >= oldest:
        buckets.append(cursor)
        cursor -= window

    digest_entries: List[DigestEntry] = []
    for bucket_start in reversed(buckets):
        bucket_end = bucket_start + window
        window_rollups = [
            e for e in rollup_entries
            if bucket_start <= date.fromisoformat(e.from_version[:10]) < bucket_end
        ]
        if not window_rollups:
            continue
        total = sum(e.total for e in window_rollups)
        tables: set = set()
        type_counts: Dict[str, int] = {}
        for e in window_rollups:
            for ct, cnt in e.count_by_type.items():
                type_counts[ct] = type_counts.get(ct, 0) + cnt
            tables.update(e.tables_affected)
        digest_entries.append(
            DigestEntry(
                period=bucket_start.isoformat(),
                window_days=window_days,
                total_changes=total,
                tables_affected=len(tables),
                top_change_types=type_counts,
            )
        )

    return ChangeDigest(entries=digest_entries)
