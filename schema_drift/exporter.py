"""Export audit reports and diff results to various file formats."""

from __future__ import annotations

import csv
import io
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from schema_drift.audit import AuditReport
    from schema_drift.diff import DiffResult


def export_diff_csv(diff: "DiffResult") -> str:
    """Serialize a DiffResult to a CSV string."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["change_type", "table", "column", "detail"])
    for change in diff.changes:
        writer.writerow([
            change.change_type.value,
            change.table,
            change.column or "",
            change.detail or "",
        ])
    return output.getvalue()


def export_audit_csv(report: "AuditReport") -> str:
    """Serialize an AuditReport to a CSV string (one row per change per entry)."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["from_version", "to_version", "captured_at", "change_type", "table", "column", "detail"])
    for entry in report.entries:
        if not entry.has_changes():
            writer.writerow([
                entry.diff.from_version,
                entry.diff.to_version,
                entry.captured_at.isoformat(),
                "", "", "", "",
            ])
            continue
        for change in entry.diff.changes:
            writer.writerow([
                entry.diff.from_version,
                entry.diff.to_version,
                entry.captured_at.isoformat(),
                change.change_type.value,
                change.table,
                change.column or "",
                change.detail or "",
            ])
    return output.getvalue()


def export_audit_json(report: "AuditReport") -> str:
    """Serialize an AuditReport to a JSON string."""
    data = [
        {
            "from_version": entry.diff.from_version,
            "to_version": entry.diff.to_version,
            "captured_at": entry.captured_at.isoformat(),
            "changes": [
                {
                    "change_type": c.change_type.value,
                    "table": c.table,
                    "column": c.column,
                    "detail": c.detail,
                }
                for c in entry.diff.changes
            ],
        }
        for entry in report.entries
    ]
    return json.dumps(data, indent=2)


def export_audit(report: "AuditReport", fmt: str = "json") -> str:
    """Export an AuditReport in the requested format ('json' or 'csv')."""
    if fmt == "csv":
        return export_audit_csv(report)
    if fmt == "json":
        return export_audit_json(report)
    raise ValueError(f"Unsupported export format: {fmt!r}. Choose 'json' or 'csv'.")
