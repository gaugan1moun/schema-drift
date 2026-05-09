"""Comparator module: compare two snapshots and produce a ranked summary of changes."""

from dataclasses import dataclass, field
from typing import List, Dict

from schema_drift.diff import DiffResult, ChangeType, compute_diff
from schema_drift.snapshot import SchemaSnapshot


@dataclass
class RankedChange:
    """A schema change annotated with a severity score."""
    table: str
    column: str
    change_type: ChangeType
    severity: int  # 1=low, 2=medium, 3=high
    detail: str = ""


_SEVERITY: Dict[ChangeType, int] = {
    ChangeType.TABLE_REMOVED: 3,
    ChangeType.TABLE_ADDED: 1,
    ChangeType.COLUMN_REMOVED: 3,
    ChangeType.COLUMN_ADDED: 1,
    ChangeType.COLUMN_TYPE_CHANGED: 2,
    ChangeType.COLUMN_NULLABLE_CHANGED: 2,
}


@dataclass
class ComparisonResult:
    """Full comparison between two snapshots with ranked changes."""
    diff: DiffResult
    ranked: List[RankedChange] = field(default_factory=list)

    @property
    def has_high_severity(self) -> bool:
        return any(r.severity == 3 for r in self.ranked)

    @property
    def summary(self) -> Dict[str, int]:
        counts: Dict[str, int] = {"high": 0, "medium": 0, "low": 0}
        for r in self.ranked:
            if r.severity == 3:
                counts["high"] += 1
            elif r.severity == 2:
                counts["medium"] += 1
            else:
                counts["low"] += 1
        return counts


def compare(base: SchemaSnapshot, updated: SchemaSnapshot) -> ComparisonResult:
    """Compute diff and rank each change by severity."""
    diff = compute_diff(base, updated)
    ranked: List[RankedChange] = []
    for change in diff.changes:
        severity = _SEVERITY.get(change.change_type, 1)
        ranked.append(
            RankedChange(
                table=change.table,
                column=change.column or "",
                change_type=change.change_type,
                severity=severity,
                detail=str(change),
            )
        )
    ranked.sort(key=lambda r: r.severity, reverse=True)
    return ComparisonResult(diff=diff, ranked=ranked)
