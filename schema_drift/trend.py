"""Trend analysis across multiple rollup entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from schema_drift.rollup import RollupEntry


@dataclass
class TrendPoint:
    """A single data point in a trend series."""
    label: str          # e.g. "2024-01" or version pair
    total_changes: int
    high_severity: int
    medium_severity: int
    low_severity: int

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "total_changes": self.total_changes,
            "high_severity": self.high_severity,
            "medium_severity": self.medium_severity,
            "low_severity": self.low_severity,
        }


@dataclass
class TrendReport:
    """Trend report built from a sequence of rollup entries."""
    points: List[TrendPoint] = field(default_factory=list)

    @property
    def is_empty(self) -> bool:
        return len(self.points) == 0

    def peak(self) -> Optional[TrendPoint]:
        """Return the point with the highest total changes."""
        if self.is_empty:
            return None
        return max(self.points, key=lambda p: p.total_changes)

    def average_changes(self) -> float:
        """Return the mean number of changes across all points."""
        if self.is_empty:
            return 0.0
        return sum(p.total_changes for p in self.points) / len(self.points)

    def is_increasing(self) -> bool:
        """Return True if the last point exceeds the first."""
        if len(self.points) < 2:
            return False
        return self.points[-1].total_changes > self.points[0].total_changes

    def to_dict(self) -> dict:
        return {
            "points": [p.to_dict() for p in self.points],
            "average_changes": self.average_changes(),
            "peak_label": self.peak().label if self.peak() else None,
            "is_increasing": self.is_increasing(),
        }


def build_trend(entries: List[RollupEntry]) -> TrendReport:
    """Build a TrendReport from an ordered list of RollupEntry objects."""
    points: List[TrendPoint] = []
    for entry in entries:
        counts = entry.count_by_type
        high = counts.get("TABLE_REMOVED", 0) + counts.get("COLUMN_REMOVED", 0)
        medium = counts.get("COLUMN_TYPE_CHANGED", 0) + counts.get("COLUMN_RENAMED", 0)
        low = counts.get("TABLE_ADDED", 0) + counts.get("COLUMN_ADDED", 0)
        points.append(TrendPoint(
            label=f"{entry.from_version} -> {entry.to_version}",
            total_changes=entry.total_changes,
            high_severity=high,
            medium_severity=medium,
            low_severity=low,
        ))
    return TrendReport(points=points)
