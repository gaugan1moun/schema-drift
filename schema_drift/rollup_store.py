"""Persist and retrieve RollupReports from disk."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import List

from schema_drift.rollup import RollupEntry, RollupReport


_DATE_FMT = "%Y%m%d"


class RollupStore:
    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, period_start: datetime) -> Path:
        label = period_start.strftime(_DATE_FMT)
        return self.directory / f"rollup_{label}.json"

    def save(self, report: RollupReport) -> Path:
        path = self._path(report.period_start)
        path.write_text(json.dumps(report.to_dict(), indent=2))
        return path

    def load(self, period_start: datetime) -> RollupReport:
        path = self._path(period_start)
        if not path.exists():
            raise FileNotFoundError(f"No rollup found for {period_start.date()}: {path}")
        data = json.loads(path.read_text())
        return _report_from_dict(data)

    def list_reports(self) -> List[RollupReport]:
        reports = []
        for p in sorted(self.directory.glob("rollup_*.json")):
            data = json.loads(p.read_text())
            reports.append(_report_from_dict(data))
        return reports


def _entry_from_dict(d: dict) -> RollupEntry:
    return RollupEntry(
        from_version=d["from_version"],
        to_version=d["to_version"],
        captured_at=datetime.fromisoformat(d["captured_at"]),
        total_changes=d["total_changes"],
        added_columns=d["added_columns"],
        removed_columns=d["removed_columns"],
        modified_columns=d["modified_columns"],
        added_tables=d["added_tables"],
        removed_tables=d["removed_tables"],
    )


def _report_from_dict(d: dict) -> RollupReport:
    return RollupReport(
        period_start=datetime.fromisoformat(d["period_start"]),
        period_end=datetime.fromisoformat(d["period_end"]),
        entries=[_entry_from_dict(e) for e in d.get("entries", [])],
    )
