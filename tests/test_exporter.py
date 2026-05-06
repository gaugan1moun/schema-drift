"""Tests for schema_drift.exporter."""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone

import pytest

from schema_drift.diff import ChangeType, DiffResult, SchemaChange
from schema_drift.audit import AuditEntry, AuditReport
from schema_drift.exporter import (
    export_diff_csv,
    export_audit_csv,
    export_audit_json,
    export_audit,
)


@pytest.fixture()
def sample_diff() -> DiffResult:
    changes = [
        SchemaChange(change_type=ChangeType.COLUMN_ADDED, table="users", column="email", detail=None),
        SchemaChange(change_type=ChangeType.TABLE_REMOVED, table="legacy", column=None, detail=None),
    ]
    return DiffResult(from_version="v1", to_version="v2", changes=changes)


@pytest.fixture()
def sample_report(sample_diff) -> AuditReport:
    entry = AuditEntry(
        diff=sample_diff,
        captured_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
    )
    return AuditReport(entries=[entry])


def test_export_diff_csv_headers(sample_diff):
    result = export_diff_csv(sample_diff)
    reader = csv.reader(io.StringIO(result))
    headers = next(reader)
    assert headers == ["change_type", "table", "column", "detail"]


def test_export_diff_csv_row_count(sample_diff):
    result = export_diff_csv(sample_diff)
    rows = list(csv.reader(io.StringIO(result)))
    # header + 2 changes
    assert len(rows) == 3


def test_export_diff_csv_values(sample_diff):
    result = export_diff_csv(sample_diff)
    rows = list(csv.reader(io.StringIO(result)))
    assert rows[1][0] == ChangeType.COLUMN_ADDED.value
    assert rows[1][1] == "users"
    assert rows[1][2] == "email"


def test_export_audit_csv_includes_version_columns(sample_report):
    result = export_audit_csv(sample_report)
    reader = csv.reader(io.StringIO(result))
    headers = next(reader)
    assert "from_version" in headers
    assert "to_version" in headers
    assert "captured_at" in headers


def test_export_audit_json_is_valid_json(sample_report):
    result = export_audit_json(sample_report)
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 1


def test_export_audit_json_structure(sample_report):
    data = json.loads(export_audit_json(sample_report))
    entry = data[0]
    assert entry["from_version"] == "v1"
    assert entry["to_version"] == "v2"
    assert len(entry["changes"]) == 2


def test_export_audit_dispatches_json(sample_report):
    result = export_audit(sample_report, fmt="json")
    assert result == export_audit_json(sample_report)


def test_export_audit_dispatches_csv(sample_report):
    result = export_audit(sample_report, fmt="csv")
    assert result == export_audit_csv(sample_report)


def test_export_audit_invalid_format_raises(sample_report):
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_audit(sample_report, fmt="xml")
