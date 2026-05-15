"""Renders an OwnershipReport in text, markdown, and JSON formats."""
from __future__ import annotations

import json

from schema_drift.change_ownership import OwnershipReport


def render_text(report: OwnershipReport) -> str:
    lines = [
        f"Ownership Report  {report.from_version} -> {report.to_version}",
        "=" * 50,
    ]
    if report.is_empty():
        lines.append("No changes to assign.")
        return "\n".join(lines)

    by_owner = report.by_owner()
    for owner, changes in sorted(by_owner.items()):
        lines.append(f"\nOwner: {owner} ({len(changes)} change(s))")
        for oc in changes:
            col_part = f".{oc.change.column}" if oc.change.column else ""
            lines.append(f"  [{oc.change.change_type.value}] {oc.change.table}{col_part}")

    if report.unowned:
        lines.append(f"\nUnowned ({len(report.unowned)} change(s))")
        for c in report.unowned:
            col_part = f".{c.column}" if c.column else ""
            lines.append(f"  [{c.change_type.value}] {c.table}{col_part}")

    return "\n".join(lines)


def render_markdown(report: OwnershipReport) -> str:
    lines = [
        f"## Ownership Report: `{report.from_version}` → `{report.to_version}`",
    ]
    if report.is_empty():
        lines.append("_No changes to assign._")
        return "\n".join(lines)

    by_owner = report.by_owner()
    for owner, changes in sorted(by_owner.items()):
        lines.append(f"\n### {owner}")
        for oc in changes:
            col_part = f".{oc.change.column}" if oc.change.column else ""
            lines.append(f"- `[{oc.change.change_type.value}]` `{oc.change.table}{col_part}`")

    if report.unowned:
        lines.append("\n### _(unowned)_")
        for c in report.unowned:
            col_part = f".{c.column}" if c.column else ""
            lines.append(f"- `[{c.change_type.value}]` `{c.table}{col_part}`")

    return "\n".join(lines)


def render_json(report: OwnershipReport) -> str:
    return json.dumps(report.to_dict(), indent=2)


def render(report: OwnershipReport, fmt: str = "text") -> str:
    if fmt == "markdown":
        return render_markdown(report)
    if fmt == "json":
        return render_json(report)
    return render_text(report)
