"""Compute change velocity: rate of schema changes over time windows."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from schema_drift.rollup import RollupEntry


@dataclass
class VelocityPoint:
    window_start: datetime
    window_end: datetime
    change_count: int
    tables_affected: int

    def to_dict(self) -> dict:
        return {
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "change_count": self.change_count,
            "tables_affected": self.tables_affected,
        }


@dataclass
class VelocityReport:
    window_days: int
    points: List[VelocityPoint] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.points) == 0

    def peak(self) -> Optional[VelocityPoint]:
        if self.is_empty():
            return None
        return max(self.points, key=lambda p: p.change_count)

    def average_changes(self) -> float:
        if self.is_empty():
            return 0.0
        return sum(p.change_count for p in self.points) / len(self.points)

    def to_dict(self) -> dict:
        return {
            "window_days": self.window_days,
            "average_changes": round(self.average_changes(), 2),
            "peak": self.peak().to_dict() if self.peak() else None,
            "points": [p.to_dict() for p in self.points],
        }


def build_velocity_report(
    entries: List[RollupEntry],
    window_days: int = 7,
) -> VelocityReport:
    """Aggregate rollup entries into fixed-size time windows."""
    if not entries:
        return VelocityReport(window_days=window_days)

    sorted_entries = sorted(entries, key=lambda e: e.from_version)
    start = datetime.fromisoformat(sorted_entries[0].from_version[:10])
    end = datetime.fromisoformat(sorted_entries[-1].from_version[:10])

    points: List[VelocityPoint] = []
    cursor = start
    while cursor <= end:
        window_end = cursor + timedelta(days=window_days)
        window_entries = [
            e for e in sorted_entries
            if cursor <= datetime.fromisoformat(e.from_version[:10]) < window_end
        ]
        total_changes = sum(e.total_changes for e in window_entries)
        tables = set()
        for e in window_entries:
            tables.update(e.tables_affected)
        points.append(VelocityPoint(
            window_start=cursor,
            window_end=window_end,
            change_count=total_changes,
            tables_affected=len(tables),
        ))
        cursor = window_end

    return VelocityReport(window_days=window_days, points=points)
