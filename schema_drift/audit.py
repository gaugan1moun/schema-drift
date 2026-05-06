"""High-level audit helpers: diff consecutive snapshots in history."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from schema_drift.diff import DiffResult, diff_snapshots
from schema_drift.history import SnapshotHistory


@dataclass
class AuditEntry:
    """A diff between two consecutive snapshots."""

    from_version: str
    to_version: str
    result: DiffResult

    @property
    def has_changes(self) -> bool:
        return self.result.has_changes


@dataclass
class AuditReport:
    """Collection of all consecutive diffs across the full history."""

    entries: List[AuditEntry] = field(default_factory=list)

    @property
    def total_changes(self) -> int:
        return sum(len(e.result.changes) for e in self.entries)

    @property
    def versions_with_changes(self) -> List[str]:
        return [e.to_version for e in self.entries if e.has_changes]

    @property
    def has_any_changes(self) -> bool:
        """Return True if at least one entry in the report contains changes."""
        return any(e.has_changes for e in self.entries)


def audit_history(history: SnapshotHistory) -> AuditReport:
    """Diff every consecutive pair of snapshots stored in *history*.

    Returns an :class:`AuditReport` with one :class:`AuditEntry` per pair.
    If fewer than two snapshots exist the report will be empty.
    """
    report = AuditReport()
    versions = history.list_versions()
    if len(versions) < 2:
        return report

    for i in range(1, len(versions)):
        prev_ver = versions[i - 1]
        curr_ver = versions[i]

        prev_snap = history.load(_unsafe(prev_ver))
        curr_snap = history.load(_unsafe(curr_ver))

        result = diff_snapshots(prev_snap, curr_snap)
        report.entries.append(
            AuditEntry(
                from_version=prev_snap.version,
                to_version=curr_snap.version,
                result=result,
            )
        )

    return report


def _unsafe(safe_name: str) -> str:
    """Reverse the safe-name transformation used by SnapshotHistory (best-effort)."""
    # SnapshotHistory stores files as <safe>.json where safe = version with / -> _
    # We just pass the stem directly to history.load which re-applies the transform.
    return safe_name
