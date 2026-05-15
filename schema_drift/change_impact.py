"""Estimate the impact of schema changes based on affected tables and change types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from schema_drift.diff import DiffResult, ChangeType


IMPACT_WEIGHTS: Dict[ChangeType, int] = {
    ChangeType.TABLE_REMOVED: 10,
    ChangeType.COLUMN_REMOVED: 7,
    ChangeType.COLUMN_TYPE_CHANGED: 5,
    ChangeType.TABLE_ADDED: 2,
    ChangeType.COLUMN_ADDED: 1,
}


def impact_score_for(change_type: ChangeType) -> int:
    """Return the impact score for a single change type."""
    return IMPACT_WEIGHTS.get(change_type, 0)


@dataclass
class TableImpact:
    table: str
    score: int
    change_count: int

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "score": self.score,
            "change_count": self.change_count,
        }


@dataclass
class ImpactReport:
    from_version: str
    to_version: str
    total_score: int
    table_impacts: List[TableImpact] = field(default_factory=list)

    def is_empty(self) -> bool:
        return self.total_score == 0

    def most_impacted_table(self) -> TableImpact | None:
        if not self.table_impacts:
            return None
        return max(self.table_impacts, key=lambda t: t.score)

    def to_dict(self) -> dict:
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "total_score": self.total_score,
            "table_impacts": [t.to_dict() for t in self.table_impacts],
        }


def build_impact_report(diff: DiffResult) -> ImpactReport:
    """Build an ImpactReport from a DiffResult."""
    table_scores: Dict[str, int] = {}
    table_counts: Dict[str, int] = {}

    for change in diff.changes:
        score = impact_score_for(change.change_type)
        table_scores[change.table] = table_scores.get(change.table, 0) + score
        table_counts[change.table] = table_counts.get(change.table, 0) + 1

    table_impacts = [
        TableImpact(table=t, score=table_scores[t], change_count=table_counts[t])
        for t in sorted(table_scores, key=lambda t: -table_scores[t])
    ]

    total = sum(t.score for t in table_impacts)
    return ImpactReport(
        from_version=diff.from_version,
        to_version=diff.to_version,
        total_score=total,
        table_impacts=table_impacts,
    )
