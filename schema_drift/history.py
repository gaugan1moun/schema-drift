"""Manages a persistent history of schema snapshots on disk."""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from schema_drift.serializer import dump, load
from schema_drift.snapshot import SchemaSnapshot


class SnapshotHistory:
    """Stores and retrieves an ordered list of snapshots from a directory."""

    def __init__(self, history_dir: str | Path) -> None:
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(parents=True, exist_ok=True)

    def _snapshot_path(self, version: str) -> Path:
        safe = version.replace("/", "_").replace(" ", "_")
        return self.history_dir / f"{safe}.json"

    def save(self, snapshot: SchemaSnapshot) -> Path:
        """Persist a snapshot to disk. Returns the file path written."""
        path = self._snapshot_path(snapshot.version)
        with open(path, "w", encoding="utf-8") as fh:
            dump(snapshot, fh)
        return path

    def load(self, version: str) -> SchemaSnapshot:
        """Load a snapshot by version string. Raises FileNotFoundError if missing."""
        path = self._snapshot_path(version)
        with open(path, "r", encoding="utf-8") as fh:
            return load(fh)

    def list_versions(self) -> List[str]:
        """Return all stored versions, sorted by file modification time (oldest first)."""
        files = sorted(
            self.history_dir.glob("*.json"),
            key=lambda p: p.stat().st_mtime,
        )
        return [p.stem for p in files]

    def latest(self) -> Optional[SchemaSnapshot]:
        """Return the most recently saved snapshot, or None if history is empty."""
        versions = self.list_versions()
        if not versions:
            return None
        version = versions[-1].replace("_", "/", 1)  # best-effort reverse of safe name
        path = self.history_dir / f"{versions[-1]}.json"
        with open(path, "r", encoding="utf-8") as fh:
            return load(fh)

    def previous(self, version: str) -> Optional[SchemaSnapshot]:
        """Return the snapshot that precedes *version*, or None if it is the first."""
        versions = self.list_versions()
        safe = version.replace("/", "_").replace(" ", "_")
        if safe not in versions:
            raise KeyError(f"Version {version!r} not found in history.")
        idx = versions.index(safe)
        if idx == 0:
            return None
        path = self.history_dir / f"{versions[idx - 1]}.json"
        with open(path, "r", encoding="utf-8") as fh:
            return load(fh)
