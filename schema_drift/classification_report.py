"""Render ClassificationResult in text, markdown, and JSON formats."""
from __future__ import annotations

import json
from typing import IO

from schema_drift.change_classifier import ClassificationResult, RISK_LEVEL_ORDER

_RISK_ICON = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🟠",
    "critical": "🔴",
    "none": "⚪",
}


def render_text(result: ClassificationResult, out: IO[str] | None = None) -> str:
    lines = [
        f"Classification: {result.from_version} → {result.to_version}",
        f"Highest risk: {_RISK_ICON.get(result.highest_risk, '')} {result.highest_risk.upper()}",
        "",
    ]
    if not result.classified:
        lines.append("  No changes detected.")
    else:
        for level in reversed(RISK_LEVEL_ORDER):
            group = result.by_risk(level)
            if group:
                lines.append(f"  [{level.upper()}]")
                for c in group:
                    col_part = f".{c.change.column}" if c.change.column else ""
                    lines.append(f"    {c.change.change_type.value}: {c.change.table}{col_part}")
    text = "\n".join(lines)
    if out is not None:
        out.write(text)
    return text


def render_markdown(result: ClassificationResult, out: IO[str] | None = None) -> str:
    lines = [
        f"## Schema Classification: `{result.from_version}` → `{result.to_version}`",
        f"**Highest risk:** {_RISK_ICON.get(result.highest_risk, '')} `{result.highest_risk.upper()}`",
        "",
    ]
    if not result.classified:
        lines.append("_No changes detected._")
    else:
        for level in reversed(RISK_LEVEL_ORDER):
            group = result.by_risk(level)
            if group:
                lines.append(f"### {_RISK_ICON.get(level, '')} {level.capitalize()}")
                for c in group:
                    col_part = f"`.{c.change.column}`" if c.change.column else ""
                    lines.append(f"- **{c.change.change_type.value}**: `{c.change.table}`{col_part}")
                lines.append("")
    text = "\n".join(lines)
    if out is not None:
        out.write(text)
    return text


def render_json(result: ClassificationResult, out: IO[str] | None = None) -> str:
    text = json.dumps(result.to_dict(), indent=2)
    if out is not None:
        out.write(text)
    return text


def render(result: ClassificationResult, fmt: str = "text", out: IO[str] | None = None) -> str:
    if fmt == "markdown":
        return render_markdown(result, out)
    if fmt == "json":
        return render_json(result, out)
    return render_text(result, out)
