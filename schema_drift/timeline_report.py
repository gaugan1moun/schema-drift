"""Render a ChangeTimeline in multiple output formats."""
from __future__ import annotations

import json
from typing import Literal

from schema_drift.change_timeline import ChangeTimeline


def render_text(timeline: ChangeTimeline) -> str:
    if timeline.is_empty():
        return "No timeline events found."
    lines = ["Schema Change Timeline", "=" * 40]
    for ev in timeline.events:
        col_part = f" (column: {ev.column})" if ev.column else ""
        lines.append(
            f"[{ev.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
            f"{ev.from_version} -> {ev.to_version} | "
            f"{ev.table}{col_part}: {ev.change_type.value}"
        )
    return "\n".join(lines)


def render_markdown(timeline: ChangeTimeline) -> str:
    if timeline.is_empty():
        return "_No timeline events found._"
    lines = ["## Schema Change Timeline", ""]
    lines.append("| Timestamp | From | To | Table | Column | Change |")
    lines.append("|---|---|---|---|---|---|")
    for ev in timeline.events:
        col = ev.column or ""
        lines.append(
            f"| {ev.timestamp.strftime('%Y-%m-%d %H:%M:%S')} "
            f"| {ev.from_version} | {ev.to_version} "
            f"| {ev.table} | {col} | {ev.change_type.value} |"
        )
    return "\n".join(lines)


def render_json(timeline: ChangeTimeline) -> str:
    return json.dumps(timeline.to_dict(), indent=2)


def render(
    timeline: ChangeTimeline,
    fmt: Literal["text", "markdown", "json"] = "text",
) -> str:
    if fmt == "markdown":
        return render_markdown(timeline)
    if fmt == "json":
        return render_json(timeline)
    return render_text(timeline)
