"""Persist and retrieve SnapshotDiffSummary records."""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from schema_drift.snapshot_diff_summary import SnapshotDiffSummary


class SummaryStore:
    """File-backed store for SnapshotDiffSummary objects.

    Each summary is written as a JSON file named
    ``<from_version>__<to_version>.json`` inside *directory*.
    """

    def __init__(self, directory: str | Path) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, from_version: str, to_version: str) -> Path:
        safe_from = from_version.replace("/", "_")
        safe_to = to_version.replace("/", "_")
        return self._dir / f"{safe_from}__{safe_to}.json"

    def save(self, summary: SnapshotDiffSummary) -> Path:
        """Persist *summary* and return the file path written."""
        path = self._path(summary.from_version, summary.to_version)
        path.write_text(json.dumps(summary.to_dict(), indent=2), encoding="utf-8")
        return path

    def load(self, from_version: str, to_version: str) -> SnapshotDiffSummary:
        """Load a summary by version pair; raises FileNotFoundError if absent."""
        path = self._path(from_version, to_version)
        data = json.loads(path.read_text(encoding="utf-8"))
        return SnapshotDiffSummary(
            from_version=data["from_version"],
            to_version=data["to_version"],
            total_changes=data["total_changes"],
            counts_by_type=data.get("counts_by_type", {}),
            affected_tables=data.get("affected_tables", []),
        )

    def exists(self, from_version: str, to_version: str) -> bool:
        return self._path(from_version, to_version).exists()

    def list_all(self) -> List[SnapshotDiffSummary]:
        """Return all stored summaries sorted by filename."""
        summaries: List[SnapshotDiffSummary] = []
        for p in sorted(self._dir.glob("*.json")):
            data = json.loads(p.read_text(encoding="utf-8"))
            summaries.append(
                SnapshotDiffSummary(
                    from_version=data["from_version"],
                    to_version=data["to_version"],
                    total_changes=data["total_changes"],
                    counts_by_type=data.get("counts_by_type", {}),
                    affected_tables=data.get("affected_tables", []),
                )
            )
        return summaries

    def delete(self, from_version: str, to_version: str) -> bool:
        """Delete a stored summary; returns True if it existed."""
        path = self._path(from_version, to_version)
        if path.exists():
            path.unlink()
            return True
        return False
