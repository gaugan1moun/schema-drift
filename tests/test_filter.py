"""Tests for schema_drift.filter."""

import pytest

from schema_drift.diff import ChangeType, DiffResult, SchemaChange
from schema_drift.filter import (
    DiffFilter,
    apply_filter,
    changes_by_table,
    unique_tables,
)


@pytest.fixture()
def sample_diff() -> DiffResult:
    return DiffResult(
        from_version="v1",
        to_version="v2",
        changes=[
            SchemaChange(table="users", change_type=ChangeType.COLUMN_ADDED, column="email"),
            SchemaChange(table="users", change_type=ChangeType.COLUMN_REMOVED, column="phone"),
            SchemaChange(table="orders", change_type=ChangeType.COLUMN_ADDED, column="total"),
            SchemaChange(table="products", change_type=ChangeType.TABLE_REMOVED, column=None),
        ],
    )


def test_filter_by_table(sample_diff):
    f = DiffFilter(tables=["users"])
    result = apply_filter(sample_diff, f)
    assert all(c.table == "users" for c in result.changes)
    assert len(result.changes) == 2


def test_filter_by_change_type(sample_diff):
    f = DiffFilter(change_types=[ChangeType.COLUMN_ADDED])
    result = apply_filter(sample_diff, f)
    assert all(c.change_type == ChangeType.COLUMN_ADDED for c in result.changes)
    assert len(result.changes) == 2


def test_filter_excludes_table(sample_diff):
    f = DiffFilter(exclude_tables=["products"])
    result = apply_filter(sample_diff, f)
    assert all(c.table != "products" for c in result.changes)
    assert len(result.changes) == 3


def test_filter_combined(sample_diff):
    f = DiffFilter(tables=["users", "orders"], change_types=[ChangeType.COLUMN_ADDED])
    result = apply_filter(sample_diff, f)
    assert len(result.changes) == 2
    assert all(c.change_type == ChangeType.COLUMN_ADDED for c in result.changes)


def test_filter_preserves_versions(sample_diff):
    result = apply_filter(sample_diff, DiffFilter())
    assert result.from_version == "v1"
    assert result.to_version == "v2"


def test_filter_no_criteria_returns_all(sample_diff):
    result = apply_filter(sample_diff, DiffFilter())
    assert len(result.changes) == len(sample_diff.changes)


def test_unique_tables(sample_diff):
    tables = unique_tables(sample_diff)
    assert tables == {"users", "orders", "products"}


def test_changes_by_table(sample_diff):
    grouped = changes_by_table(sample_diff)
    assert set(grouped.keys()) == {"users", "orders", "products"}
    assert len(grouped["users"]) == 2
    assert len(grouped["orders"]) == 1


def test_filter_empty_diff():
    empty = DiffResult(from_version="v1", to_version="v2", changes=[])
    result = apply_filter(empty, DiffFilter(tables=["users"]))
    assert result.changes == []
