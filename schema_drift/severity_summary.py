"""Aggregate severity statistics across a DiffResult or AuditReport."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from schema_drift.diff import ChangeType, DiffResult
from schema_drift.audit import AuditReport


_SEVERITY_RANK: Dict[str, int] = {
    "critical": 3,
    "high": 2,
    "medium": 1,
    "low": 0,
}

_CHANGE_SEVERITY: Dict[ChangeType, str] = {
    ChangeType.TABLE_REMOVED: "critical",
    ChangeType.COLUMN_REMOVED: "high",
    ChangeType.TYPE_CHANGED: "high",
    ChangeType.TABLE_ADDED: "medium",
    ChangeType.COLUMN_ADDED: "medium",
    ChangeType.NULLABLE_CHANGED: "low",
    ChangeType.DEFAULT_CHANGED: "low",
}


def severity_for(change_type: ChangeType) -> str:
    """Return a severity label for a given ChangeType."""
    return _CHANGE_SEVERITY.get(change_type, "low")


@dataclass
class SeveritySummary:
    counts: Dict[str, int] = field(default_factory=lambda: {"critical": 0, "high": 0, "medium": 0, "low": 0})
    highest: str = "low"

    def total(self) -> int:
        return sum(self.counts.values())

    def is_empty(self) -> bool:
        return self.total() == 0

    def to_dict(self) -> dict:
        return {"counts": dict(self.counts), "highest": self.highest, "total": self.total()}


def summarise_diff(diff: DiffResult) -> SeveritySummary:
    """Build a SeveritySummary from a single DiffResult."""
    counts: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for change in diff.changes:
        sev = severity_for(change.change_type)
        counts[sev] += 1
    highest = max(counts, key=lambda k: (_SEVERITY_RANK[k], counts[k]))
    if counts[highest] == 0:
        highest = "low"
    return SeveritySummary(counts=counts, highest=highest)


def summarise_audit(report: AuditReport) -> SeveritySummary:
    """Aggregate severity counts across all entries in an AuditReport."""
    counts: Dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for entry in report.entries:
        for change in entry.diff.changes:
            sev = severity_for(change.change_type)
            counts[sev] += 1
    highest = max(counts, key=lambda k: (_SEVERITY_RANK[k], counts[k]))
    if counts[highest] == 0:
        highest = "low"
    return SeveritySummary(counts=counts, highest=highest)
