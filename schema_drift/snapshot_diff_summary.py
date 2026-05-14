"""Snapshot diff summary: aggregate statistics across a DiffResult."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from schema_drift.diff import ChangeType, DiffResult


@dataclass
class SnapshotDiffSummary:
    """High-level statistics derived from a DiffResult."""

    from_version: str
    to_version: str
    total_changes: int
    counts_by_type: Dict[str, int] = field(default_factory=dict)
    affected_tables: List[str] = field(default_factory=list)

    def is_empty(self) -> bool:
        return self.total_changes == 0

    def to_dict(self) -> dict:
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "total_changes": self.total_changes,
            "counts_by_type": self.counts_by_type,
            "affected_tables": self.affected_tables,
        }


def build_summary(diff: DiffResult) -> SnapshotDiffSummary:
    """Build a SnapshotDiffSummary from a DiffResult."""
    counts: Dict[str, int] = {ct.value: 0 for ct in ChangeType}
    tables: set = set()

    for change in diff.changes:
        counts[change.change_type.value] = counts.get(change.change_type.value, 0) + 1
        tables.add(change.table)

    # Remove zero-count entries for a cleaner output
    counts = {k: v for k, v in counts.items() if v > 0}

    return SnapshotDiffSummary(
        from_version=diff.from_version,
        to_version=diff.to_version,
        total_changes=len(diff.changes),
        counts_by_type=counts,
        affected_tables=sorted(tables),
    )


def render_text(summary: SnapshotDiffSummary) -> str:
    lines = [
        f"Diff Summary: {summary.from_version} -> {summary.to_version}",
        f"  Total changes : {summary.total_changes}",
    ]
    if summary.counts_by_type:
        lines.append("  By type:")
        for change_type, count in sorted(summary.counts_by_type.items()):
            lines.append(f"    {change_type}: {count}")
    if summary.affected_tables:
        lines.append(f"  Affected tables ({len(summary.affected_tables)}): " +
                     ", ".join(summary.affected_tables))
    return "\n".join(lines)


def render_markdown(summary: SnapshotDiffSummary) -> str:
    lines = [
        f"## Diff Summary: `{summary.from_version}` → `{summary.to_version}`",
        f"- **Total changes**: {summary.total_changes}",
    ]
    if summary.counts_by_type:
        lines.append("\n### Changes by type")
        for change_type, count in sorted(summary.counts_by_type.items()):
            lines.append(f"- `{change_type}`: {count}")
    if summary.affected_tables:
        table_list = ", ".join(f"`{t}`" for t in summary.affected_tables)
        lines.append(f"\n### Affected tables ({len(summary.affected_tables)})")
        lines.append(table_list)
    return "\n".join(lines)
