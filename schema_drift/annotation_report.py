"""Render annotations alongside diff results for enriched reporting."""

from __future__ import annotations

import json
from typing import Optional

from schema_drift.annotator import AnnotationStore
from schema_drift.diff import DiffResult, SchemaChange


def _annotation_note(store: AnnotationStore, table: str, column: Optional[str]) -> str:
    annotations = store.get(table, column)
    if not annotations:
        return ""
    return " | ".join(a.note for a in annotations)


def render_text(diff: DiffResult, store: AnnotationStore) -> str:
    """Render a plain-text diff report enriched with annotations."""
    lines = [f"Schema diff: {diff.from_version} -> {diff.to_version}"]
    if not diff.has_changes():
        lines.append("  No changes detected.")
        return "\n".join(lines)

    for change in diff.changes:
        note = _annotation_note(store, change.table, change.column)
        suffix = f"  [note: {note}]" if note else ""
        col_part = f".{change.column}" if change.column else ""
        lines.append(f"  [{change.change_type.value}] {change.table}{col_part}{suffix}")

    return "\n".join(lines)


def render_markdown(diff: DiffResult, store: AnnotationStore) -> str:
    """Render a Markdown diff report enriched with annotations."""
    lines = [f"## Schema Diff: `{diff.from_version}` → `{diff.to_version}`", ""]
    if not diff.has_changes():
        lines.append("_No changes detected._")
        return "\n".join(lines)

    lines.append("| Change | Target | Annotation |")
    lines.append("|--------|--------|------------|")
    for change in diff.changes:
        note = _annotation_note(store, change.table, change.column) or "—"
        col_part = f".{change.column}" if change.column else ""
        lines.append(f"| {change.change_type.value} | `{change.table}{col_part}` | {note} |")

    return "\n".join(lines)


def render_json(diff: DiffResult, store: AnnotationStore) -> str:
    """Render a JSON diff report enriched with annotations."""
    changes = []
    for change in diff.changes:
        note = _annotation_note(store, change.table, change.column)
        entry = {
            "change_type": change.change_type.value,
            "table": change.table,
            "column": change.column,
            "annotation": note or None,
        }
        changes.append(entry)

    payload = {
        "from_version": diff.from_version,
        "to_version": diff.to_version,
        "changes": changes,
    }
    return json.dumps(payload, indent=2)


def render(diff: DiffResult, store: AnnotationStore, fmt: str = "text") -> str:
    """Dispatch to the appropriate renderer."""
    if fmt == "markdown":
        return render_markdown(diff, store)
    if fmt == "json":
        return render_json(diff, store)
    return render_text(diff, store)
