"""Watch a snapshot file for changes and emit diffs automatically."""

from __future__ import annotations

import time
import os
from pathlib import Path
from typing import Callable, Optional

from schema_drift.serializer import load
from schema_drift.diff import diff_snapshots, DiffResult
from schema_drift.snapshot import SchemaSnapshot


class SnapshotWatcher:
    """Poll a snapshot file and invoke a callback when the schema changes."""

    def __init__(
        self,
        path: str | Path,
        on_change: Callable[[DiffResult], None],
        poll_interval: float = 5.0,
    ) -> None:
        self.path = Path(path)
        self.on_change = on_change
        self.poll_interval = poll_interval
        self._last_mtime: Optional[float] = None
        self._last_snapshot: Optional[SchemaSnapshot] = None

    def _current_mtime(self) -> Optional[float]:
        try:
            return os.path.getmtime(self.path)
        except FileNotFoundError:
            return None

    def _load(self) -> Optional[SchemaSnapshot]:
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                return load(fh)
        except (FileNotFoundError, ValueError):
            return None

    def check_once(self) -> Optional[DiffResult]:
        """Check for a change. Returns a DiffResult if the snapshot changed."""
        mtime = self._current_mtime()
        if mtime is None:
            return None

        if mtime == self._last_mtime:
            return None

        snapshot = self._load()
        if snapshot is None:
            return None

        result: Optional[DiffResult] = None
        if self._last_snapshot is not None:
            result = diff_snapshots(self._last_snapshot, snapshot)
            if result.has_changes():
                self.on_change(result)

        self._last_mtime = mtime
        self._last_snapshot = snapshot
        return result

    def watch(self, max_iterations: Optional[int] = None) -> None:
        """Block and poll indefinitely (or up to *max_iterations* cycles)."""
        iterations = 0
        while True:
            self.check_once()
            iterations += 1
            if max_iterations is not None and iterations >= max_iterations:
                break
            time.sleep(self.poll_interval)
