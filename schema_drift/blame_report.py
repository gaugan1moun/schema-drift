"""Rendering utilities for BlameReport."""
from __future__ import annotations

import json
from typing import Optional

from schema_drift.change_blame import BlameReport


def render_text(report: BlameReport) -> str:
    lines = [f"Blame Report: {report.from_version} -> {report.to_version}"]
    if report.is_empty():
        lines.append("  No changes to blame.")
        return "\n".join(lines)
    for owner, changes in sorted(report.by_owner().items()):
        lines.append(f"\n  Owner: {owner}")
        for bc in changes:
            col_part = f" (column: {bc.change.column})" if bc.change.column else ""
            lines.append(f"    [{bc.change.change_type.value}] {bc.change.table}{col_part}")
    return "\n".join(lines)


def render_markdown(report: BlameReport) -> str:
    lines = [f"## Blame Report: `{report.from_version}` → `{report.to_version}`"]
    if report.is_empty():
        lines.append("_No changes to blame._")
        return "\n".join(lines)
    for owner, changes in sorted(report.by_owner().items()):
        lines.append(f"\n### {owner}")
        lines.append("| Table | Change | Column |")
        lines.append("|-------|--------|--------|")
        for bc in changes:
            col = bc.change.column or ""
            lines.append(f"| {bc.change.table} | {bc.change.change_type.value} | {col} |")
    return "\n".join(lines)


def render_json(report: BlameReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def render(report: BlameReport, fmt: str = "text") -> str:
    if fmt == "markdown":
        return render_markdown(report)
    if fmt == "json":
        return render_json(report)
    return render_text(report)
