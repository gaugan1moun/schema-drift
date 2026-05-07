"""Tag-based labeling and filtering for schema snapshots."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from schema_drift.snapshot import SchemaSnapshot


@dataclass
class TaggedSnapshot:
    """A snapshot decorated with a set of string tags."""

    snapshot: SchemaSnapshot
    tags: List[str] = field(default_factory=list)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    def add_tag(self, tag: str) -> None:
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        self.tags = [t for t in self.tags if t != tag]


@dataclass
class TagIndex:
    """Maintains a mapping from tag -> list of snapshot versions."""

    _index: Dict[str, List[str]] = field(default_factory=dict)

    def register(self, tagged: TaggedSnapshot) -> None:
        version = tagged.snapshot.version
        for tag in tagged.tags:
            self._index.setdefault(tag, [])
            if version not in self._index[tag]:
                self._index[tag].append(version)

    def versions_for_tag(self, tag: str) -> List[str]:
        return list(self._index.get(tag, []))

    def tags_for_version(self, version: str) -> List[str]:
        return [tag for tag, versions in self._index.items() if version in versions]

    def all_tags(self) -> List[str]:
        return list(self._index.keys())


def filter_by_tag(
    tagged_snapshots: List[TaggedSnapshot], tag: str
) -> List[TaggedSnapshot]:
    """Return only those TaggedSnapshots that carry *tag*."""
    return [ts for ts in tagged_snapshots if ts.has_tag(tag)]


def filter_by_any_tag(
    tagged_snapshots: List[TaggedSnapshot], tags: List[str]
) -> List[TaggedSnapshot]:
    """Return snapshots that carry at least one of *tags*."""
    tag_set = set(tags)
    return [ts for ts in tagged_snapshots if tag_set.intersection(ts.tags)]
