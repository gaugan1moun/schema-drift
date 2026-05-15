"""Render a CorrelationReport in various formats."""
from __future__ import annotations

import json
from typing import Optional

from schema_drift.change_correlation import CorrelationReport


def render_text(report: CorrelationReport, top_n: int = 5) -> str:
    lines = [f"Change Correlation Report ({report.total_versions_analyzed} versions analyzed)"]
    lines.append("=" * 55)
    if report.is_empty():
        lines.append("No co-changing table pairs detected.")
        return "\n".join(lines)

    lines.append(f"Top {top_n} correlated table pairs:")
    for pair in report.top_pairs(top_n):
        lines.append(
            f"  {pair.table_a} <-> {pair.table_b}: "
            f"{pair.co_change_count} co-changes "
            f"(ratio: {pair.correlation_ratio:.2%})"
        )
    return "\n".join(lines)


def render_markdown(report: CorrelationReport, top_n: int = 5) -> str:
    lines = ["## Change Correlation Report"]
    lines.append(f"_Versions analyzed: {report.total_versions_analyzed}_")
    lines.append("")
    if report.is_empty():
        lines.append("_No co-changing table pairs detected._")
        return "\n".join(lines)

    lines.append(f"### Top {top_n} Correlated Pairs")
    lines.append("")
    lines.append("| Table A | Table B | Co-changes | Ratio |")
    lines.append("|---------|---------|------------|-------|")
    for pair in report.top_pairs(top_n):
        lines.append(
            f"| {pair.table_a} | {pair.table_b} | "
            f"{pair.co_change_count} | {pair.correlation_ratio:.2%} |"
        )
    return "\n".join(lines)


def render_json(report: CorrelationReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def render(report: CorrelationReport, fmt: str = "text", top_n: int = 5) -> str:
    if fmt == "markdown":
        return render_markdown(report, top_n=top_n)
    if fmt == "json":
        return render_json(report)
    return render_text(report, top_n=top_n)
