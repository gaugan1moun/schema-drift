"""Formats and outputs DiffResult reports in various formats."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Literal

from schema_drift.diff import DiffResult, ChangeType

OutputFormat = Literal["text", "json", "markdown"]


def _change_symbol(change_type: ChangeType) -> str:
    return {
        ChangeType.ADDED: "+",
        ChangeType.REMOVED: "-",
        ChangeType.MODIFIED: "~",
    }[change_type]


def render_text(result: DiffResult) -> str:
    lines = [
        f"Schema Diff: v{result.base_version} → v{result.updated_version}",
        f"Generated at: {datetime.utcnow().isoformat()}Z",
        "-" * 50,
    ]
    if not result.has_changes():
        lines.append("No schema changes detected.")
        return "\n".join(lines)

    for change in result.changes:
        symbol = _change_symbol(change.change_type)
        lines.append(f"[{symbol}] {change.table}.{change.column} — {change.description}")

    lines.append("-" * 50)
    lines.append(f"Total changes: {len(result.changes)}")
    return "\n".join(lines)


def render_markdown(result: DiffResult) -> str:
    lines = [
        f"## Schema Diff: `v{result.base_version}` → `v{result.updated_version}`\n",
        "| Change | Table | Column | Description |",
        "|--------|-------|--------|-------------|" ,
    ]
    if not result.has_changes():
        return "\n".join(lines) + "\n\n_No schema changes detected._"

    for change in result.changes:
        symbol = _change_symbol(change.change_type)
        lines.append(f"| `{symbol}` | `{change.table}` | `{change.column}` | {change.description} |")

    lines.append(f"\n**Total changes:** {len(result.changes)}")
    return "\n".join(lines)


def render_json(result: DiffResult) -> str:
    payload = {
        "base_version": result.base_version,
        "updated_version": result.updated_version,
        "has_changes": result.has_changes(),
        "changes": [
            {
                "change_type": change.change_type.value,
                "table": change.table,
                "column": change.column,
                "description": change.description,
            }
            for change in result.changes
        ],
    }
    return json.dumps(payload, indent=2)


def render(result: DiffResult, fmt: OutputFormat = "text") -> str:
    """Render a DiffResult in the requested format."""
    if fmt == "json":
        return render_json(result)
    if fmt == "markdown":
        return render_markdown(result)
    return render_text(result)
