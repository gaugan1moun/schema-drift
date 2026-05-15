"""Persist and load RetentionPolicy configurations."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from schema_drift.change_retention import RetentionPolicy


class RetentionStore:
    def __init__(self, directory: str | Path) -> None:
        self._dir = Path(directory)

    def _path(self) -> Path:
        return self._dir / "retention_policy.json"

    def save(self, policy: RetentionPolicy) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        data = {
            "max_entries": policy.max_entries,
            "max_age_days": policy.max_age_days,
            "keep_versions_with_changes": policy.keep_versions_with_changes,
        }
        self._path().write_text(json.dumps(data, indent=2))

    def load(self) -> RetentionPolicy:
        p = self._path()
        if not p.exists():
            raise FileNotFoundError(f"No retention policy found at {p}")
        data = json.loads(p.read_text())
        return RetentionPolicy(
            max_entries=data.get("max_entries"),
            max_age_days=data.get("max_age_days"),
            keep_versions_with_changes=data.get("keep_versions_with_changes", True),
        )

    def exists(self) -> bool:
        return self._path().exists()

    def delete(self) -> None:
        p = self._path()
        if p.exists():
            p.unlink()
