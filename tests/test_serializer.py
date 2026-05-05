"""Tests for schema_drift.serializer module."""

import io
import json
from datetime import datetime, timezone

import pytest

from schema_drift.snapshot import ColumnSchema, TableSchema, SchemaSnapshot
from schema_drift import serializer


@pytest.fixture
def sample_snapshot():
    col_id = ColumnSchema(name="id", data_type="INTEGER", nullable=False, default=None)
    col_name = ColumnSchema(name="name", data_type="VARCHAR", nullable=True, default="''")
    table = TableSchema(name="users", columns={"id": col_id, "name": col_name})
    return SchemaSnapshot(
        version="v1.2.0",
        captured_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        tables={"users": table},
    )


def test_snapshot_to_dict_structure(sample_snapshot):
    result = serializer.snapshot_to_dict(sample_snapshot)
    assert result["version"] == "v1.2.0"
    assert "captured_at" in result
    assert "users" in result["tables"]
    assert "id" in result["tables"]["users"]["columns"]


def test_snapshot_to_dict_column_fields(sample_snapshot):
    result = serializer.snapshot_to_dict(sample_snapshot)
    col = result["tables"]["users"]["columns"]["id"]
    assert col["name"] == "id"
    assert col["data_type"] == "INTEGER"
    assert col["nullable"] is False
    assert col["default"] is None


def test_dumps_produces_valid_json(sample_snapshot):
    output = serializer.dumps(sample_snapshot)
    parsed = json.loads(output)
    assert parsed["version"] == "v1.2.0"


def test_loads_roundtrip(sample_snapshot):
    json_str = serializer.dumps(sample_snapshot)
    restored = serializer.loads(json_str)
    assert restored.version == sample_snapshot.version
    assert restored.captured_at == sample_snapshot.captured_at
    assert set(restored.tables.keys()) == set(sample_snapshot.tables.keys())


def test_loads_restores_columns(sample_snapshot):
    json_str = serializer.dumps(sample_snapshot)
    restored = serializer.loads(json_str)
    col = restored.tables["users"].columns["name"]
    assert col.data_type == "VARCHAR"
    assert col.nullable is True
    assert col.default == "''"


def test_dump_and_load_file_roundtrip(sample_snapshot):
    buf = io.StringIO()
    serializer.dump(sample_snapshot, buf)
    buf.seek(0)
    restored = serializer.load(buf)
    assert restored.version == sample_snapshot.version
    assert "users" in restored.tables


def test_snapshot_from_dict_missing_tables():
    data = {
        "version": "v0.1",
        "captured_at": "2024-01-01T00:00:00",
        "tables": {},
    }
    snapshot = serializer.snapshot_from_dict(data)
    assert snapshot.version == "v0.1"
    assert snapshot.tables == {}
