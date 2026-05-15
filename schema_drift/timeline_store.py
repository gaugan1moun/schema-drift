"""Persist and load ChangeTimeline objects to/from disk."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from schema_drift.change_timeline import ChangeTimeline, TimelineEvent
from schema_drift.diff import ChangeType


class TimelineStore:
    def __init__(self, directory: str | Path) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self) -> Path:
        return self._dir / "timeline.json"

    def save(self, timeline: ChangeTimeline) -> None:
        self._path().write_text(json.dumps(timeline.to_dict(), indent=2))

    def load(self) -> ChangeTimeline:
        p = self._path()
        if not p.exists():
            raise FileNotFoundError(f"Timeline not found: {p}")
        raw = json.loads(p.read_text())
        events = [
            TimelineEvent(
                timestamp=datetime.fromisoformat(e["timestamp"]),
                from_version=e["from_version"],
                to_version=e["to_version"],
                table=e["table"],
                change_type=ChangeType(e["change_type"]),
                column=e.get("column"),
            )
            for e in raw.get("events", [])
        ]
        return ChangeTimeline(events=events)

    def exists(self) -> bool:
        return self._path().exists()

    def append(self, other: ChangeTimeline) -> None:
        """Merge *other* into the persisted timeline (dedup by identity)."""
        existing = self.load() if self.exists() else ChangeTimeline()
        seen = {(e.timestamp, e.from_version, e.to_version, e.table, e.column) for e in existing.events}
        for ev in other.events:
            key = (ev.timestamp, ev.from_version, ev.to_version, ev.table, ev.column)
            if key not in seen:
                existing.events.append(ev)
                seen.add(key)
        existing.events.sort(key=lambda e: e.timestamp)
        self.save(existing)
