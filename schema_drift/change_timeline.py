"""Build and query a chronological timeline of schema changes."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from schema_drift.audit import AuditEntry
from schema_drift.diff import ChangeType


@dataclass
class TimelineEvent:
    timestamp: datetime
    from_version: str
    to_version: str
    table: str
    change_type: ChangeType
    column: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "from_version": self.from_version,
            "to_version": self.to_version,
            "table": self.table,
            "change_type": self.change_type.value,
            "column": self.column,
        }


@dataclass
class ChangeTimeline:
    events: List[TimelineEvent] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.events) == 0

    def for_table(self, table: str) -> "ChangeTimeline":
        return ChangeTimeline(events=[e for e in self.events if e.table == table])

    def for_change_type(self, change_type: ChangeType) -> "ChangeTimeline":
        return ChangeTimeline(events=[e for e in self.events if e.change_type == change_type])

    def since(self, dt: datetime) -> "ChangeTimeline":
        return ChangeTimeline(events=[e for e in self.events if e.timestamp >= dt])

    def to_dict(self) -> dict:
        return {"events": [e.to_dict() for e in self.events]}


def build_timeline(entries: List[AuditEntry]) -> ChangeTimeline:
    """Flatten audit entries into a sorted list of timeline events."""
    events: List[TimelineEvent] = []
    for entry in entries:
        ts = entry.diff.captured_at if hasattr(entry.diff, "captured_at") else datetime.utcnow()
        for change in entry.diff.changes:
            events.append(
                TimelineEvent(
                    timestamp=ts,
                    from_version=entry.diff.from_version,
                    to_version=entry.diff.to_version,
                    table=change.table,
                    change_type=change.change_type,
                    column=change.column,
                )
            )
    events.sort(key=lambda e: e.timestamp)
    return ChangeTimeline(events=events)
