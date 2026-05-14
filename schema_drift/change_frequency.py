"""Compute per-table and per-column change frequency from rollup history."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from schema_drift.rollup import RollupEntry, RollupReport


@dataclass
class TableFrequency:
    table: str
    change_count: int
    versions_seen: int

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "change_count": self.change_count,
            "versions_seen": self.versions_seen,
        }


@dataclass
class ChangeFrequencyReport:
    table_frequencies: List[TableFrequency] = field(default_factory=list)

    def most_changed_table(self) -> TableFrequency | None:
        if not self.table_frequencies:
            return None
        return max(self.table_frequencies, key=lambda t: t.change_count)

    def least_changed_table(self) -> TableFrequency | None:
        if not self.table_frequencies:
            return None
        return min(self.table_frequencies, key=lambda t: t.change_count)

    def sorted_by_frequency(self, descending: bool = True) -> List[TableFrequency]:
        return sorted(
            self.table_frequencies,
            key=lambda t: t.change_count,
            reverse=descending,
        )

    def tables_above_threshold(self, threshold: int) -> List[TableFrequency]:
        """Return tables whose change count exceeds the given threshold.

        Args:
            threshold: Minimum change count (exclusive) to include a table.

        Returns:
            List of TableFrequency entries with change_count > threshold.
        """
        return [tf for tf in self.table_frequencies if tf.change_count > threshold]

    def to_dict(self) -> dict:
        return {
            "table_frequencies": [tf.to_dict() for tf in self.table_frequencies]
        }


def build_frequency_report(reports: List[RollupReport]) -> ChangeFrequencyReport:
    """Aggregate change counts per table across multiple RollupReports."""
    table_counts: Dict[str, int] = {}
    table_versions: Dict[str, set] = {}

    for report in reports:
        for entry in report.entries:
            version_key = f"{entry.from_version}->{entry.to_version}"
            for table, count in entry.changes_by_table.items():
                table_counts[table] = table_counts.get(table, 0) + count
                if table not in table_versions:
                    table_versions[table] = set()
                table_versions[table].add(version_key)

    frequencies = [
        TableFrequency(
            table=table,
            change_count=count,
            versions_seen=len(table_versions.get(table, set())),
        )
        for table, count in table_counts.items()
    ]

    return ChangeFrequencyReport(table_frequencies=frequencies)
