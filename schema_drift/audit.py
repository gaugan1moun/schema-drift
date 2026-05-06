"""Audit trail: accumulate and summarise multiple DiffResults over time."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from schema_drift.diff import DiffResult


@dataclass
class AuditEntry:
    """A single recorded diff with a timestamp."""

    diff: DiffResult
    captured_at: datetime = field(default_factory=lambda: datetime.now(tz=timezone.utc))

    def has_changes(self) -> bool:
        """Return True if the wrapped diff contains any changes."""
        return self.diff.has_changes()


@dataclass
class AuditReport:
    """Collection of AuditEntry objects representing a history of diffs."""

    entries: List[AuditEntry] = field(default_factory=list)

    def total_changes(self) -> int:
        """Return the total number of individual schema changes across all entries."""
        return sum(len(e.diff.changes) for e in self.entries)

    def versions_with_changes(self) -> List[str]:
        """Return a list of to_version strings where changes were detected."""
        return [
            e.diff.to_version
            for e in self.entries
            if e.has_changes()
        ]

    def add_entry(self, diff: DiffResult, captured_at: Optional[datetime] = None) -> AuditEntry:
        """Create and append a new AuditEntry for *diff*."""
        entry = AuditEntry(
            diff=diff,
            captured_at=captured_at or datetime.now(tz=timezone.utc),
        )
        self.entries.append(entry)
        return entry

    def entries_with_changes(self) -> List[AuditEntry]:
        """Return only the entries that contain at least one change."""
        return [e for e in self.entries if e.has_changes()]

    def summary(self) -> dict:
        """Return a high-level summary dict suitable for display or serialisation."""
        return {
            "total_entries": len(self.entries),
            "entries_with_changes": len(self.entries_with_changes()),
            "total_changes": self.total_changes(),
            "versions_with_changes": self.versions_with_changes(),
        }
