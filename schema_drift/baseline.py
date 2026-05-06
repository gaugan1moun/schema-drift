"""Baseline management for schema snapshots.

Allows pinning a snapshot as the official baseline and comparing
any subsequent snapshot against it.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from schema_drift.snapshot import SchemaSnapshot
from schema_drift.serializer import snapshot_to_dict, snapshot_from_dict
from schema_drift.diff import DiffResult, compute_diff

_DEFAULT_BASELINE_FILE = "baseline.json"


class BaselineManager:
    """Persist and retrieve a pinned baseline snapshot."""

    def __init__(self, directory: str | Path = ".") -> None:
        self.directory = Path(directory)
        self._path = self.directory / _DEFAULT_BASELINE_FILE

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, snapshot: SchemaSnapshot) -> None:
        """Write *snapshot* to disk as the current baseline."""
        self.directory.mkdir(parents=True, exist_ok=True)
        data = snapshot_to_dict(snapshot)
        self._path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def load(self) -> SchemaSnapshot:
        """Load and return the persisted baseline snapshot.

        Raises
        ------
        FileNotFoundError
            If no baseline has been saved yet.
        """
        if not self._path.exists():
            raise FileNotFoundError(
                f"No baseline found at '{self._path}'. "
                "Run 'schema-drift baseline set <snapshot>' first."
            )
        data = json.loads(self._path.read_text(encoding="utf-8"))
        return snapshot_from_dict(data)

    def exists(self) -> bool:
        """Return True when a baseline file is present on disk."""
        return self._path.exists()

    def clear(self) -> None:
        """Remove the baseline file if it exists."""
        if self._path.exists():
            self._path.unlink()

    # ------------------------------------------------------------------
    # Comparison
    # ------------------------------------------------------------------

    def diff_against(self, snapshot: SchemaSnapshot) -> DiffResult:
        """Compare the saved baseline against *snapshot*.

        Returns a :class:`~schema_drift.diff.DiffResult` describing every
        schema change between the baseline and the provided snapshot.
        """
        baseline = self.load()
        return compute_diff(baseline, snapshot)
