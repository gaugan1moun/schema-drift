"""Compute a numeric risk score for a diff or audit report."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from schema_drift.diff import DiffResult, ChangeType

# Weight assigned to each change type
_WEIGHTS: dict[ChangeType, int] = {
    ChangeType.TABLE_REMOVED: 10,
    ChangeType.COLUMN_REMOVED: 8,
    ChangeType.COLUMN_TYPE_CHANGED: 6,
    ChangeType.COLUMN_NULLABLE_CHANGED: 4,
    ChangeType.TABLE_ADDED: 2,
    ChangeType.COLUMN_ADDED: 1,
}

_THRESHOLDS = {
    "low": 10,
    "medium": 30,
    "high": 60,
}


def weight_for(change_type: ChangeType) -> int:
    """Return the numeric weight for a single change type."""
    return _WEIGHTS.get(change_type, 1)


@dataclass
class ScoredDiff:
    from_version: str
    to_version: str
    score: int
    breakdown: dict = field(default_factory=dict)

    @property
    def risk_level(self) -> str:
        if self.score >= _THRESHOLDS["high"]:
            return "critical"
        if self.score >= _THRESHOLDS["medium"]:
            return "high"
        if self.score >= _THRESHOLDS["low"]:
            return "medium"
        return "low"

    def to_dict(self) -> dict:
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "score": self.score,
            "risk_level": self.risk_level,
            "breakdown": {k.value: v for k, v in self.breakdown.items()},
        }


def score_diff(diff: DiffResult) -> ScoredDiff:
    """Compute a ScoredDiff from a DiffResult."""
    breakdown: dict[ChangeType, int] = {}
    total = 0
    for change in diff.changes:
        w = weight_for(change.change_type)
        breakdown[change.change_type] = breakdown.get(change.change_type, 0) + w
        total += w
    return ScoredDiff(
        from_version=diff.from_version,
        to_version=diff.to_version,
        score=total,
        breakdown=breakdown,
    )


def score_multiple(diffs: List[DiffResult]) -> List[ScoredDiff]:
    """Score a list of DiffResults and return them in order."""
    return [score_diff(d) for d in diffs]
