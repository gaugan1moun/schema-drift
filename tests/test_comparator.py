"""Tests for schema_drift.comparator."""

import pytest
from datetime import datetime, timezone

from schema_drift.snapshot import SchemaSnapshot, TableSchema, ColumnSchema
from schema_drift.diff import ChangeType
from schema_drift.comparator import compare, ComparisonResult


def _col(name: str, dtype: str = "TEXT", nullable: bool = True) -> ColumnSchema:
    return ColumnSchema(name=name, data_type=dtype, nullable=nullable)


def _snap(version: str, tables) -> SchemaSnapshot:
    return SchemaSnapshot(
        version=version,
        captured_at=datetime.now(timezone.utc),
        tables={t.name: t for t in tables},
    )


@pytest.fixture
def base():
    return _snap("v1", [
        TableSchema(name="users", columns={"id": _col("id", "INT", False), "email": _col("email")}),
        TableSchema(name="orders", columns={"id": _col("id", "INT", False)}),
    ])


@pytest.fixture
def updated():
    return _snap("v2", [
        TableSchema(name="users", columns={"id": _col("id", "BIGINT", False), "email": _col("email")}),
    ])


def test_compare_returns_comparison_result(base, updated):
    result = compare(base, updated)
    assert isinstance(result, ComparisonResult)


def test_compare_diff_has_changes(base, updated):
    result = compare(base, updated)
    assert result.diff.has_changes


def test_ranked_sorted_by_severity_descending(base, updated):
    result = compare(base, updated)
    severities = [r.severity for r in result.ranked]
    assert severities == sorted(severities, reverse=True)


def test_table_removed_is_high_severity(base, updated):
    result = compare(base, updated)
    removals = [r for r in result.ranked if r.change_type == ChangeType.TABLE_REMOVED]
    assert removals, "expected at least one TABLE_REMOVED"
    assert all(r.severity == 3 for r in removals)


def test_column_type_changed_is_medium_severity(base, updated):
    result = compare(base, updated)
    type_changes = [r for r in result.ranked if r.change_type == ChangeType.COLUMN_TYPE_CHANGED]
    assert type_changes, "expected a COLUMN_TYPE_CHANGED entry"
    assert all(r.severity == 2 for r in type_changes)


def test_has_high_severity_true(base, updated):
    result = compare(base, updated)
    assert result.has_high_severity is True


def test_has_high_severity_false_when_no_changes():
    snap = _snap("v1", [TableSchema(name="t", columns={"a": _col("a")})])
    result = compare(snap, snap)
    assert result.has_high_severity is False


def test_summary_counts(base, updated):
    result = compare(base, updated)
    s = result.summary
    assert s["high"] >= 1
    assert s["medium"] >= 1
    assert isinstance(s["low"], int)
