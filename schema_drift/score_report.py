"""Render a ScoredDiff or list of ScoredDiffs as text / markdown / JSON."""
from __future__ import annotations

import json
from typing import List

from schema_drift.change_score import ScoredDiff

_RISK_EMOJI = {
    "low": "🟢",
    "medium": "🟡",
    "high": "🔴",
    "critical": "💀",
}


def render_text(scored: ScoredDiff) -> str:
    lines = [
        f"Score Report: {scored.from_version} → {scored.to_version}",
        f"  Total score : {scored.score}",
        f"  Risk level  : {scored.risk_level.upper()}",
    ]
    if scored.breakdown:
        lines.append("  Breakdown:")
        for change_type, pts in sorted(scored.breakdown.items(), key=lambda x: -x[1]):
            lines.append(f"    {change_type.value:<30} {pts:>4} pts")
    return "\n".join(lines)


def render_markdown(scored: ScoredDiff) -> str:
    emoji = _RISK_EMOJI.get(scored.risk_level, "")
    lines = [
        f"## Score Report: `{scored.from_version}` → `{scored.to_version}`",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total score | **{scored.score}** |",
        f"| Risk level | {emoji} **{scored.risk_level.upper()}** |",
    ]
    if scored.breakdown:
        lines += ["", "### Breakdown", "", "| Change Type | Points |", "|-------------|--------|"]
        for ct, pts in sorted(scored.breakdown.items(), key=lambda x: -x[1]):
            lines.append(f"| `{ct.value}` | {pts} |")
    return "\n".join(lines)


def render_json(scored: ScoredDiff) -> str:
    return json.dumps(scored.to_dict(), indent=2)


def render(scored: ScoredDiff, fmt: str = "text") -> str:
    if fmt == "markdown":
        return render_markdown(scored)
    if fmt == "json":
        return render_json(scored)
    return render_text(scored)
