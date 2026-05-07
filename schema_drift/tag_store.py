"""Persist and retrieve TaggedSnapshot metadata (tags only) as JSON."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


_FILENAME = "tags.json"


class TagStore:
    """Stores tag assignments keyed by snapshot version in a JSON file."""

    def __init__(self, directory: str | Path) -> None:
        self._dir = Path(directory)
        self._path = self._dir / _FILENAME
        self._data: Dict[str, List[str]] = self._load()

    def _load(self) -> Dict[str, List[str]]:
        if self._path.exists():
            with self._path.open() as fh:
                return json.load(fh)
        return {}

    def _save(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        with self._path.open("w") as fh:
            json.dump(self._data, fh, indent=2)

    def set_tags(self, version: str, tags: List[str]) -> None:
        self._data[version] = list(tags)
        self._save()

    def get_tags(self, version: str) -> List[str]:
        return list(self._data.get(version, []))

    def add_tag(self, version: str, tag: str) -> None:
        current = self._data.get(version, [])
        if tag not in current:
            current.append(tag)
            self._data[version] = current
            self._save()

    def remove_tag(self, version: str, tag: str) -> None:
        current = self._data.get(version, [])
        self._data[version] = [t for t in current if t != tag]
        self._save()

    def all_versions(self) -> List[str]:
        return list(self._data.keys())

    def versions_with_tag(self, tag: str) -> List[str]:
        return [v for v, tags in self._data.items() if tag in tags]
