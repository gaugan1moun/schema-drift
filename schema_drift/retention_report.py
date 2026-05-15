"""Render RetentionResult in multiple formats."""
from __future__ import annotations

import json

from schema_drift.change_retention import RetentionResult


def render_text(result: RetentionResult) -> str:
    lines = ["=== Retention Report ==="]
    lines.append(f"Kept   : {result.kept_count} entries")
    lines.append(f"Pruned : {result.pruned_count} entries")
    if result.pruned:
        lines.append("Pruned versions:")
        for e in result.pruned:
            lines.append(f"  - {e.version_from} -> {e.version_to}  ({e.total_changes} changes)")
    else:
        lines.append("No entries were pruned.")
    return "\n".join(lines)


def render_markdown(result: RetentionResult) -> str:
    lines = ["## Retention Report", ""]
    lines.append(f"- **Kept**: {result.kept_count}")
    lines.append(f"- **Pruned**: {result.pruned_count}")
    if result.pruned:
        lines.append("\n### Pruned Entries")
        lines.append("| From | To | Changes |")
        lines.append("|------|----|---------|")
        for e in result.pruned:
            lines.append(f"| {e.version_from} | {e.version_to} | {e.total_changes} |")
    return "\n".join(lines)


def render_json(result: RetentionResult) -> str:
    return json.dumps(result.to_dict(), indent=2)


def render(result: RetentionResult, fmt: str = "text") -> str:
    if fmt == "markdown":
        return render_markdown(result)
    if fmt == "json":
        return render_json(result)
    return render_text(result)
