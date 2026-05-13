"""Render RollupReports in text, markdown, and JSON formats."""
from __future__ import annotations

import json

from schema_drift.rollup import RollupReport


def render_text(report: RollupReport) -> str:
    lines = [
        f"Rollup Period: {report.period_start.date()} to {report.period_end.date()}",
        f"Total Changes : {report.total_changes}",
        f"Diff Entries  : {len(report.entries)}",
    ]
    if report.most_active_version_pair:
        lines.append(f"Most Active   : {report.most_active_version_pair}")
    if not report.entries:
        lines.append("  (no diffs recorded)")
    else:
        lines.append("")
        for e in report.entries:
            lines.append(
                f"  {e.from_version} -> {e.to_version}: "
                f"+{e.added_columns} col, -{e.removed_columns} col, "
                f"~{e.modified_columns} col, "
                f"+{e.added_tables} tbl, -{e.removed_tables} tbl"
            )
    return "\n".join(lines)


def render_markdown(report: RollupReport) -> str:
    lines = [
        f"## Rollup: {report.period_start.date()} — {report.period_end.date()}",
        "",
        f"**Total changes:** {report.total_changes}  ",
        f"**Diff entries:** {len(report.entries)}  ",
    ]
    if report.most_active_version_pair:
        lines.append(f"**Most active pair:** `{report.most_active_version_pair}`  ")
    if report.entries:
        lines += [
            "",
            "| From | To | Added | Removed | Modified | +Tables | -Tables |",
            "|------|----|----|---------|----------|---------|---------|" ,
        ]
        for e in report.entries:
            lines.append(
                f"| {e.from_version} | {e.to_version} "
                f"| {e.added_columns} | {e.removed_columns} "
                f"| {e.modified_columns} | {e.added_tables} | {e.removed_tables} |"
            )
    return "\n".join(lines)


def render_json(report: RollupReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def render(report: RollupReport, fmt: str = "text") -> str:
    if fmt == "markdown":
        return render_markdown(report)
    if fmt == "json":
        return render_json(report)
    return render_text(report)
