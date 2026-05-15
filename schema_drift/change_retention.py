"""Change retention policy: determine which historical diffs to keep or prune."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from schema_drift.rollup import RollupEntry


@dataclass
class RetentionPolicy:
    max_entries: Optional[int] = None
    max_age_days: Optional[int] = None
    keep_versions_with_changes: bool = True


@dataclass
class RetentionResult:
    kept: List[RollupEntry] = field(default_factory=list)
    pruned: List[RollupEntry] = field(default_factory=list)

    @property
    def kept_count(self) -> int:
        return len(self.kept)

    @property
    def pruned_count(self) -> int:
        return len(self.pruned)

    def is_empty(self) -> bool:
        return len(self.kept) == 0 and len(self.pruned) == 0

    def to_dict(self) -> dict:
        return {
            "kept_count": self.kept_count,
            "pruned_count": self.pruned_count,
            "kept_versions": [e.version_from + "->" + e.version_to for e in self.kept],
            "pruned_versions": [e.version_from + "->" + e.version_to for e in self.pruned],
        }


def apply_retention(entries: List[RollupEntry], policy: RetentionPolicy) -> RetentionResult:
    """Apply a retention policy to a list of rollup entries."""
    result = RetentionResult()
    candidates = list(entries)

    if policy.max_age_days is not None:
        cutoff = datetime.utcnow() - timedelta(days=policy.max_age_days)
        kept = []
        for e in candidates:
            try:
                entry_date = datetime.fromisoformat(e.period)
            except (ValueError, AttributeError):
                kept.append(e)
                continue
            if entry_date >= cutoff:
                kept.append(e)
            elif policy.keep_versions_with_changes and e.total_changes > 0:
                kept.append(e)
            else:
                result.pruned.append(e)
        candidates = kept

    if policy.max_entries is not None and len(candidates) > policy.max_entries:
        # Sort newest-first by period, keep max_entries
        sorted_entries = sorted(
            candidates,
            key=lambda e: e.period,
            reverse=True,
        )
        kept_set = set()
        if policy.keep_versions_with_changes:
            for e in sorted_entries:
                if e.total_changes > 0 and len(kept_set) < policy.max_entries:
                    kept_set.add(id(e))
        for e in sorted_entries:
            if len(kept_set) >= policy.max_entries:
                break
            if id(e) not in kept_set:
                kept_set.add(id(e))
        for e in sorted_entries:
            if id(e) in kept_set:
                result.kept.append(e)
            else:
                result.pruned.append(e)
    else:
        result.kept.extend(candidates)

    return result
