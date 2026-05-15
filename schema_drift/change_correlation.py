"""Correlate schema changes across tables to detect co-changing patterns."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from schema_drift.audit import AuditReport


@dataclass
class CorrelationPair:
    table_a: str
    table_b: str
    co_change_count: int
    total_versions: int

    @property
    def correlation_ratio(self) -> float:
        if self.total_versions == 0:
            return 0.0
        return round(self.co_change_count / self.total_versions, 4)

    def to_dict(self) -> dict:
        return {
            "table_a": self.table_a,
            "table_b": self.table_b,
            "co_change_count": self.co_change_count,
            "total_versions": self.total_versions,
            "correlation_ratio": self.correlation_ratio,
        }


@dataclass
class CorrelationReport:
    pairs: List[CorrelationPair] = field(default_factory=list)
    total_versions_analyzed: int = 0

    def is_empty(self) -> bool:
        return len(self.pairs) == 0

    def top_pairs(self, n: int = 5) -> List[CorrelationPair]:
        return sorted(self.pairs, key=lambda p: p.correlation_ratio, reverse=True)[:n]

    def to_dict(self) -> dict:
        return {
            "total_versions_analyzed": self.total_versions_analyzed,
            "pairs": [p.to_dict() for p in self.pairs],
        }


def _tables_changed_per_version(report: AuditReport) -> List[set]:
    """Return a list of sets, each containing tables changed in that version."""
    result = []
    for entry in report.entries:
        if entry.has_changes():
            tables = {c.table for c in entry.diff.changes}
            result.append(tables)
    return result


def build_correlation_report(report: AuditReport) -> CorrelationReport:
    """Analyse co-occurrence of table changes across audit entries."""
    version_table_sets = _tables_changed_per_version(report)
    total_versions = len(version_table_sets)

    # Collect all unique tables
    all_tables: set = set()
    for ts in version_table_sets:
        all_tables.update(ts)

    all_tables_sorted = sorted(all_tables)
    co_counts: Dict[Tuple[str, str], int] = {}

    for ts in version_table_sets:
        tables_in_version = sorted(ts)
        for i, ta in enumerate(tables_in_version):
            for tb in tables_in_version[i + 1:]:
                key = (ta, tb)
                co_counts[key] = co_counts.get(key, 0) + 1

    pairs = [
        CorrelationPair(
            table_a=ta,
            table_b=tb,
            co_change_count=count,
            total_versions=total_versions,
        )
        for (ta, tb), count in co_counts.items()
    ]

    return CorrelationReport(pairs=pairs, total_versions_analyzed=total_versions)
