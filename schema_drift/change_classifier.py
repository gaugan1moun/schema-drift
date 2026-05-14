"""Classify schema changes into risk categories based on impact."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict

from schema_drift.diff import SchemaChange, ChangeType, DiffResult


RISK_LEVEL_ORDER = ["low", "medium", "high", "critical"]

_CHANGE_RISK: Dict[ChangeType, str] = {
    ChangeType.TABLE_ADDED: "low",
    ChangeType.TABLE_REMOVED: "critical",
    ChangeType.COLUMN_ADDED: "low",
    ChangeType.COLUMN_REMOVED: "high",
    ChangeType.COLUMN_TYPE_CHANGED: "high",
    ChangeType.COLUMN_NULLABLE_CHANGED: "medium",
}


def risk_for_change(change: SchemaChange) -> str:
    """Return the risk level string for a single SchemaChange."""
    return _CHANGE_RISK.get(change.change_type, "medium")


@dataclass
class ClassifiedChange:
    change: SchemaChange
    risk: str

    def to_dict(self) -> dict:
        return {
            "table": self.change.table,
            "column": self.change.column,
            "change_type": self.change.change_type.value,
            "risk": self.risk,
            "detail": self.change.detail,
        }


@dataclass
class ClassificationResult:
    from_version: str
    to_version: str
    classified: List[ClassifiedChange] = field(default_factory=list)

    def by_risk(self, level: str) -> List[ClassifiedChange]:
        return [c for c in self.classified if c.risk == level]

    @property
    def highest_risk(self) -> str:
        if not self.classified:
            return "none"
        levels = {c.risk for c in self.classified}
        for level in reversed(RISK_LEVEL_ORDER):
            if level in levels:
                return level
        return "none"

    def to_dict(self) -> dict:
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "highest_risk": self.highest_risk,
            "changes": [c.to_dict() for c in self.classified],
        }


def classify(diff: DiffResult) -> ClassificationResult:
    """Classify all changes in a DiffResult by risk level."""
    result = ClassificationResult(
        from_version=diff.from_version,
        to_version=diff.to_version,
    )
    for change in diff.changes:
        result.classified.append(
            ClassifiedChange(change=change, risk=risk_for_change(change))
        )
    return result
