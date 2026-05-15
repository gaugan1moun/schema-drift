"""Render a ChangeDigest as text, markdown, or JSON."""
from __future__ import annotations

import json
from typing import Optional

from schema_drift.change_digest import ChangeDigest


def render_text(digest: ChangeDigest) -> str:
    if digest.is_empty():
        return "No digest entries available."

    lines = ["Schema Change Digest", "=" * 40]
    for entry in digest.entries:
        lines.append(f"Period : {entry.period}  (window: {entry.window_days}d)")
        lines.append(f"  Total changes   : {entry.total_changes}")
        lines.append(f"  Tables affected : {entry.tables_affected}")
        if entry.top_change_types:
            breakdown = ", ".join(
                f"{k}: {v}" for k, v in sorted(entry.top_change_types.items())
            )
            lines.append(f"  Breakdown       : {breakdown}")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_markdown(digest: ChangeDigest) -> str:
    if digest.is_empty():
        return "_No digest entries available._"

    lines = ["## Schema Change Digest", ""]
    for entry in digest.entries:
        lines.append(f"### {entry.period} ({entry.window_days}-day window)")
        lines.append(f"- **Total changes**: {entry.total_changes}")
        lines.append(f"- **Tables affected**: {entry.tables_affected}")
        if entry.top_change_types:
            for ct, cnt in sorted(entry.top_change_types.items()):
                lines.append(f"  - `{ct}`: {cnt}")
        lines.append("")
    return "\n".join(lines).rstrip()


def render_json(digest: ChangeDigest) -> str:
    return json.dumps(digest.to_dict(), indent=2)


def render(digest: ChangeDigest, fmt: str = "text") -> str:
    fmt = fmt.lower()
    if fmt == "markdown":
        return render_markdown(digest)
    if fmt == "json":
        return render_json(digest)
    return render_text(digest)
