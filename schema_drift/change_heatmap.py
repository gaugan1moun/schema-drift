"""Build a heatmap of schema changes across tables and time periods."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from schema_drift.rollup import RollupEntry


@dataclass
class HeatmapCell:
    table: str
    period: str
    change_count: int

    def to_dict(self) -> dict:
        return {"table": self.table, "period": self.period, "change_count": self.change_count}


@dataclass
class ChangeHeatmap:
    periods: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    cells: List[HeatmapCell] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.cells) == 0

    def get(self, table: str, period: str) -> int:
        for cell in self.cells:
            if cell.table == table and cell.period == period:
                return cell.change_count
        return 0

    def hottest_cell(self) -> Optional[HeatmapCell]:
        if not self.cells:
            return None
        return max(self.cells, key=lambda c: c.change_count)

    def to_dict(self) -> dict:
        return {
            "periods": self.periods,
            "tables": self.tables,
            "cells": [c.to_dict() for c in self.cells],
        }


def build_heatmap(entries: List[RollupEntry], period_fn=None) -> ChangeHeatmap:
    """Build a ChangeHeatmap from a list of RollupEntry objects.

    Args:
        entries: Rollup entries, each representing a from_version->to_version diff.
        period_fn: Optional callable(entry) -> str to derive the period label.
                   Defaults to using entry.to_version.
    """
    if period_fn is None:
        period_fn = lambda e: e.to_version

    counts: Dict[str, Dict[str, int]] = {}  # table -> period -> count

    for entry in entries:
        period = period_fn(entry)
        for table, table_counts in entry.changes_by_table.items():
            total = sum(table_counts.values())
            counts.setdefault(table, {})
            counts[table][period] = counts[table].get(period, 0) + total

    all_tables = sorted(counts.keys())
    all_periods: List[str] = []
    seen_periods: set = set()
    for entry in entries:
        p = period_fn(entry)
        if p not in seen_periods:
            all_periods.append(p)
            seen_periods.add(p)

    cells = [
        HeatmapCell(table=t, period=p, change_count=counts[t].get(p, 0))
        for t in all_tables
        for p in all_periods
        if counts[t].get(p, 0) > 0
    ]

    return ChangeHeatmap(periods=all_periods, tables=all_tables, cells=cells)
