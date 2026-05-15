"""Render ImpactReport in text, markdown, and JSON formats."""

from __future__ import annotations

import json

from schema_drift.change_impact import ImpactReport


def render_text(report: ImpactReport) -> str:
    lines = [
        f"Impact Report: {report.from_version} -> {report.to_version}",
        f"Total Impact Score: {report.total_score}",
    ]
    if report.is_empty():
        lines.append("No schema changes detected.")
    else:
        lines.append("")
        lines.append("Table Breakdown:")
        for ti in report.table_impacts:
            lines.append(
                f"  {ti.table}: score={ti.score}, changes={ti.change_count}"
            )
        top = report.most_impacted_table()
        if top:
            lines.append("")
            lines.append(f"Most impacted table: {top.table} (score {top.score})")
    return "\n".join(lines)


def render_markdown(report: ImpactReport) -> str:
    lines = [
        f"## Impact Report: `{report.from_version}` → `{report.to_version}`",
        f"**Total Impact Score:** {report.total_score}",
        "",
    ]
    if report.is_empty():
        lines.append("_No schema changes detected._")
    else:
        lines.append("| Table | Score | Changes |")
        lines.append("|-------|-------|---------|")
        for ti in report.table_impacts:
            lines.append(f"| {ti.table} | {ti.score} | {ti.change_count} |")
        top = report.most_impacted_table()
        if top:
            lines.append("")
            lines.append(f"**Most impacted table:** `{top.table}` (score {top.score})")
    return "\n".join(lines)


def render_json(report: ImpactReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def render(report: ImpactReport, fmt: str = "text") -> str:
    if fmt == "markdown":
        return render_markdown(report)
    if fmt == "json":
        return render_json(report)
    return render_text(report)
