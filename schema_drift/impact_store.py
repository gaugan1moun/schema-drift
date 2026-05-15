"""Persist and retrieve ImpactReport instances on disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

from schema_drift.change_impact import ImpactReport, TableImpact


def _report_from_dict(d: dict) -> ImpactReport:
    table_impacts = [
        TableImpact(table=t["table"], score=t["score"], change_count=t["change_count"])
        for t in d.get("table_impacts", [])
    ]
    return ImpactReport(
        from_version=d["from_version"],
        to_version=d["to_version"],
        total_score=d["total_score"],
        table_impacts=table_impacts,
    )


class ImpactStore:
    def __init__(self, directory: str | Path) -> None:
        self._dir = Path(directory)
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, from_version: str, to_version: str) -> Path:
        safe_from = from_version.replace("/", "_")
        safe_to = to_version.replace("/", "_")
        return self._dir / f"impact_{safe_from}__{safe_to}.json"

    def save(self, report: ImpactReport) -> Path:
        p = self._path(report.from_version, report.to_version)
        p.write_text(json.dumps(report.to_dict(), indent=2))
        return p

    def load(self, from_version: str, to_version: str) -> ImpactReport:
        p = self._path(from_version, to_version)
        if not p.exists():
            raise FileNotFoundError(f"No impact report found: {p}")
        return _report_from_dict(json.loads(p.read_text()))

    def list_reports(self) -> List[ImpactReport]:
        reports = []
        for f in sorted(self._dir.glob("impact_*.json")):
            try:
                reports.append(_report_from_dict(json.loads(f.read_text())))
            except (KeyError, json.JSONDecodeError):
                continue
        return reports

    def exists(self, from_version: str, to_version: str) -> bool:
        return self._path(from_version, to_version).exists()
