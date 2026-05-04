"""Tests for schema snapshot serialization and deserialization."""

import json
import pytest
from schema_drift.snapshot import ColumnSchema, TableSchema, SchemaSnapshot


@pytest.fixture
def sample_snapshot() -> SchemaSnapshot:
    snapshot = SchemaSnapshot(version="001")
    table = TableSchema(name="users")
    table.columns = [
        ColumnSchema(name="id", data_type="INTEGER", nullable=False, primary_key=True),
        ColumnSchema(name="email", data_type="VARCHAR(255)", nullable=False),
        ColumnSchema(name="created_at", data_type="TIMESTAMP", nullable=True),
    ]
    snapshot.add_table(table)
    return snapshot


def test_snapshot_has_version(sample_snapshot):
    assert sample_snapshot.version == "001"


def test_snapshot_captured_at_is_set(sample_snapshot):
    assert sample_snapshot.captured_at is not None
    assert "T" in sample_snapshot.captured_at  # ISO format check


def test_add_table(sample_snapshot):
    assert "users" in sample_snapshot.tables


def test_get_column_found(sample_snapshot):
    col = sample_snapshot.tables["users"].get_column("email")
    assert col is not None
    assert col.data_type == "VARCHAR(255)"


def test_get_column_not_found(sample_snapshot):
    col = sample_snapshot.tables["users"].get_column("nonexistent")
    assert col is None


def test_to_dict_structure(sample_snapshot):
    d = sample_snapshot.to_dict()
    assert d["version"] == "001"
    assert "users" in d["tables"]
    assert len(d["tables"]["users"]["columns"]) == 3


def test_round_trip_json(sample_snapshot):
    json_str = sample_snapshot.to_json()
    restored = SchemaSnapshot.from_json(json_str)
    assert restored.version == sample_snapshot.version
    assert "users" in restored.tables
    col = restored.tables["users"].get_column("id")
    assert col is not None
    assert col.primary_key is True
    assert col.nullable is False


def test_from_dict_missing_tables():
    data = {"version": "002", "captured_at": "2024-01-01T00:00:00+00:00"}
    snapshot = SchemaSnapshot.from_dict(data)
    assert snapshot.tables == {}


def test_to_json_is_valid_json(sample_snapshot):
    json_str = sample_snapshot.to_json()
    parsed = json.loads(json_str)
    assert isinstance(parsed, dict)
