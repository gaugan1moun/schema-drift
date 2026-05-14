"""Render a VelocityReport in multiple output formats."""
from __future__ import annotations

import json
from typing import Literal

from schema_drift.change_velocity import VelocityReport

OutputFormat = Literal["text", "markdown", "json"]


def render_text(report: VelocityReport) -> str:
    lines = [f"Change Velocity Report  (window: {report.window_days}d)"]
    lines.append("-" * 48)
    if report.is_empty():
        lines.append("No data available.")
        return "\n".join(lines)

    lines.append(f"Average changes per window : {report.average_changes():.2f}")
    peak = report.peak()
    if peak:
        lines.append(
            f"Peak window               : {peak.window_start.date()} "
            f"– {peak.window_end.date()}  ({peak.change_count} changes)"
        )
    lines.append("")
    lines.append(f"  {'Window Start':<14}  {'Window End':<14}  {'Changes':>7}  {'Tables':>6}")
    for p in report.points:
        lines.append(
            f"  {str(p.window_start.date()):<14}  {str(p.window_end.date()):<14}"
            f"  {p.change_count:>7}  {p.tables_affected:>6}"
        )
    return "\n".join(lines)


def render_markdown(report: VelocityReport) -> str:
    lines = [f"## Change Velocity Report (window: {report.window_days}d)\n"]
    if report.is_empty():
        lines.append("_No data available._")
        return "\n".join(lines)

    lines.append(f"- **Average changes per window:** {report.average_changes():.2f}")
    peak = report.peak()
    if peak:
        lines.append(
            f"- **Peak window:** {peak.window_start.date()} – {peak.window_end.date()}"
            f" ({peak.change_count} changes)\n"
        )
    lines.append("| Window Start | Window End | Changes | Tables |")
    lines.append("|---|---|---:|---:|")
    for p in report.points:
        lines.append(
            f"| {p.window_start.date()} | {p.window_end.date()}"
            f" | {p.change_count} | {p.tables_affected} |"
        )
    return "\n".join(lines)


def render_json(report: VelocityReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def render(report: VelocityReport, fmt: OutputFormat = "text") -> str:
    if fmt == "markdown":
        return render_markdown(report)
    if fmt == "json":
        return render_json(report)
    return render_text(report)
