"""Render ComparisonResult as text, markdown, or JSON for human consumption."""

import json
from typing import Callable

from schema_drift.comparator import ComparisonResult, RankedChange

_SEVERITY_LABEL = {1: "LOW", 2: "MEDIUM", 3: "HIGH"}
_SEVERITY_EMOJI = {1: "🟢", 2: "🟡", 3: "🔴"}


def _severity_label(severity: int) -> str:
    return _SEVERITY_LABEL.get(severity, "UNKNOWN")


def render_text(result: ComparisonResult) -> str:
    lines = []
    diff = result.diff
    lines.append(f"Comparison: {diff.base_version} -> {diff.updated_version}")
    summary = result.summary
    lines.append(
        f"Changes: {len(result.ranked)} total  "
        f"| HIGH={summary['high']}  MEDIUM={summary['medium']}  LOW={summary['low']}"
    )
    if not result.ranked:
        lines.append("  No schema changes detected.")
        return "\n".join(lines)
    for r in result.ranked:
        label = _severity_label(r.severity)
        lines.append(f"  [{label}] {r.detail}")
    return "\n".join(lines)


def render_markdown(result: ComparisonResult) -> str:
    diff = result.diff
    summary = result.summary
    lines = [
        f"## Schema Comparison: `{diff.base_version}` → `{diff.updated_version}`",
        "",
        f"**Total changes:** {len(result.ranked)}  "
        f"🔴 HIGH: {summary['high']}  🟡 MEDIUM: {summary['medium']}  🟢 LOW: {summary['low']}",
        "",
    ]
    if not result.ranked:
        lines.append("_No schema changes detected._")
        return "\n".join(lines)
    lines.append("| Severity | Table | Column | Change |")
    lines.append("|----------|-------|--------|--------|")
    for r in result.ranked:
        emoji = _SEVERITY_EMOJI.get(r.severity, "")
        lines.append(f"| {emoji} {_severity_label(r.severity)} | {r.table} | {r.column or '-'} | {r.change_type.value} |")
    return "\n".join(lines)


def render_json(result: ComparisonResult) -> str:
    data = {
        "base_version": result.diff.base_version,
        "updated_version": result.diff.updated_version,
        "summary": result.summary,
        "changes": [
            {
                "table": r.table,
                "column": r.column,
                "change_type": r.change_type.value,
                "severity": _severity_label(r.severity),
                "detail": r.detail,
            }
            for r in result.ranked
        ],
    }
    return json.dumps(data, indent=2)


_RENDERERS: dict[str, Callable[[ComparisonResult], str]] = {
    "text": render_text,
    "markdown": render_markdown,
    "json": render_json,
}


def render(result: ComparisonResult, fmt: str = "text") -> str:
    renderer = _RENDERERS.get(fmt)
    if renderer is None:
        raise ValueError(f"Unknown format '{fmt}'. Choose from: {list(_RENDERERS)}.")
    return renderer(result)
