"""Tests for schema_drift.diff module."""

import pytest

from schema_drift.diff import ChangeType, diff_snapshots
from schema_drift.snapshot import ColumnSchema, SchemaSnapshot, TableSchema


@pytest.fixture
def base_snapshot() -> SchemaSnapshot:
    users = TableSchema(
        name="users",
        columns=[
            ColumnSchema(name="id", data_type="integer", nullable=False),
            ColumnSchema(name="email", data_type="varchar", nullable=False),
            ColumnSchema(name="age", data_type="integer", nullable=True),
        ],
    )
    orders = TableSchema(
        name="orders",
        columns=[
            ColumnSchema(name="id", data_type="integer", nullable=False),
            ColumnSchema(name="total", data_type="numeric", nullable=True),
        ],
    )
    return SchemaSnapshot(version="v1", tables=[users, orders])


@pytest.fixture
def updated_snapshot() -> SchemaSnapshot:
    """v2: users.age removed, users.name added, users.email nullable changed,
    orders.total type changed, products table added, orders table removed."""
    users = TableSchema(
        name="users",
        columns=[
            ColumnSchema(name="id", data_type="integer", nullable=False),
            ColumnSchema(name="email", data_type="varchar", nullable=True),  # nullable changed
            ColumnSchema(name="name", data_type="varchar", nullable=True),   # new column
        ],
    )
    products = TableSchema(
        name="products",
        columns=[
            ColumnSchema(name="id", data_type="integer", nullable=False),
            ColumnSchema(name="price", data_type="numeric", nullable=False),
        ],
    )
    return SchemaSnapshot(version="v2", tables=[users, products])


def test_diff_versions(base_snapshot, updated_snapshot):
    result = diff_snapshots(base_snapshot, updated_snapshot)
    assert result.old_version == "v1"
    assert result.new_version == "v2"


def test_diff_has_changes(base_snapshot, updated_snapshot):
    result = diff_snapshots(base_snapshot, updated_snapshot)
    assert result.has_changes


def test_table_removed(base_snapshot, updated_snapshot):
    result = diff_snapshots(base_snapshot, updated_snapshot)
    removed = [c for c in result.changes if c.change_type == ChangeType.TABLE_REMOVED]
    assert len(removed) == 1
    assert removed[0].table == "orders"


def test_table_added(base_snapshot, updated_snapshot):
    result = diff_snapshots(base_snapshot, updated_snapshot)
    added = [c for c in result.changes if c.change_type == ChangeType.TABLE_ADDED]
    assert len(added) == 1
    assert added[0].table == "products"


def test_column_removed(base_snapshot, updated_snapshot):
    result = diff_snapshots(base_snapshot, updated_snapshot)
    removed = [c for c in result.changes if c.change_type == ChangeType.COLUMN_REMOVED]
    assert any(c.table == "users" and c.column == "age" for c in removed)


def test_column_added(base_snapshot, updated_snapshot):
    result = diff_snapshots(base_snapshot, updated_snapshot)
    added = [c for c in result.changes if c.change_type == ChangeType.COLUMN_ADDED]
    assert any(c.table == "users" and c.column == "name" for c in added)


def test_column_nullable_changed(base_snapshot, updated_snapshot):
    result = diff_snapshots(base_snapshot, updated_snapshot)
    modified = [c for c in result.changes if c.change_type == ChangeType.COLUMN_MODIFIED]
    assert any(c.table == "users" and c.column == "email" for c in modified)


def test_no_changes_identical_snapshots(base_snapshot):
    """Diffing a snapshot against itself should produce no changes."""
    result = diff_snapshots(base_snapshot, base_snapshot)
    assert not result.has_changes
    assert result.changes == []
