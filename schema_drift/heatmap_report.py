"""Render a ChangeHeatmap as text, markdown, or JSON."""
from __future__ import annotations

import json

from schema_drift.change_heatmap import ChangeHeatmap


def render_text(heatmap: ChangeHeatmap) -> str:
    if heatmap.is_empty():
        return "No schema changes recorded in heatmap."

    col_width = max(len(p) for p in heatmap.periods) if heatmap.periods else 8
    col_width = max(col_width, 5)
    table_width = max((len(t) for t in heatmap.tables), default=5)

    header = f"{'Table':<{table_width}}  " + "  ".join(p.rjust(col_width) for p in heatmap.periods)
    lines = ["Schema Change Heatmap", "=" * len(header), header, "-" * len(header)]

    for table in heatmap.tables:
        row = f"{table:<{table_width}}  "
        row += "  ".join(str(heatmap.get(table, p)).rjust(col_width) for p in heatmap.periods)
        lines.append(row)

    hottest = heatmap.hottest_cell()
    if hottest:
        lines.append("")
        lines.append(f"Hottest cell: {hottest.table} @ {hottest.period} ({hottest.change_count} changes)")

    return "\n".join(lines)


def render_markdown(heatmap: ChangeHeatmap) -> str:
    if heatmap.is_empty():
        return "_No schema changes recorded in heatmap._"

    header_cols = ["Table"] + heatmap.periods
    sep_cols = ["---"] + ["---:"] * len(heatmap.periods)
    lines = [
        "## Schema Change Heatmap",
        "| " + " | ".join(header_cols) + " |",
        "| " + " | ".join(sep_cols) + " |",
    ]
    for table in heatmap.tables:
        row_vals = [table] + [str(heatmap.get(table, p)) for p in heatmap.periods]
        lines.append("| " + " | ".join(row_vals) + " |")

    hottest = heatmap.hottest_cell()
    if hottest:
        lines.append("")
        lines.append(f"**Hottest cell:** `{hottest.table}` @ `{hottest.period}` — {hottest.change_count} changes")

    return "\n".join(lines)


def render_json(heatmap: ChangeHeatmap) -> str:
    return json.dumps(heatmap.to_dict(), indent=2)


def render(heatmap: ChangeHeatmap, fmt: str = "text") -> str:
    if fmt == "markdown":
        return render_markdown(heatmap)
    if fmt == "json":
        return render_json(heatmap)
    return render_text(heatmap)
