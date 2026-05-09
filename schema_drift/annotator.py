"""Annotator module: attach human-readable notes to schema changes."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class Annotation:
    """A note attached to a specific schema change."""

    table: str
    column: Optional[str]  # None means the annotation is table-level
    note: str
    author: str = "unknown"
    created_at: str = ""

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "column": self.column,
            "note": self.note,
            "author": self.author,
            "created_at": self.created_at,
        }

    @staticmethod
    def from_dict(d: dict) -> "Annotation":
        return Annotation(
            table=d["table"],
            column=d.get("column"),
            note=d["note"],
            author=d.get("author", "unknown"),
            created_at=d.get("created_at", ""),
        )


@dataclass
class AnnotationStore:
    """Persists annotations keyed by (table, column) tuples."""

    path: Path
    _data: List[Annotation] = field(default_factory=list)

    def __post_init__(self) -> None:
        self._load()

    def _load(self) -> None:
        if self.path.exists():
            raw = json.loads(self.path.read_text())
            self._data = [Annotation.from_dict(r) for r in raw]

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps([a.to_dict() for a in self._data], indent=2))

    def add(self, annotation: Annotation) -> None:
        """Append an annotation and persist."""
        self._data.append(annotation)
        self._save()

    def get(self, table: str, column: Optional[str] = None) -> List[Annotation]:
        """Return all annotations matching table (and optionally column)."""
        return [
            a for a in self._data
            if a.table == table and a.column == column
        ]

    def all(self) -> List[Annotation]:
        return list(self._data)

    def remove(self, table: str, column: Optional[str] = None) -> int:
        """Remove matching annotations; returns count removed."""
        before = len(self._data)
        self._data = [
            a for a in self._data
            if not (a.table == table and a.column == column)
        ]
        self._save()
        return before - len(self._data)
