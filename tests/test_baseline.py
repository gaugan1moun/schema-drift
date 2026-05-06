"""Tests for schema_drift.baseline.BaselineManager."""

import json
import pytest
from pathlib import Path

from schema_drift.snapshot import SchemaSnapshot, TableSchema, ColumnSchema
from schema_drift.baseline import BaselineManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_snapshot(version: str = "v1") -> SchemaSnapshot:
    col = ColumnSchema(name="id", data_type="integer", nullable=False)
    table = TableSchema(name="users", columns=[col])
    return SchemaSnapshot(version=version, tables=[table])


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mgr(tmp_path: Path) -> BaselineManager:
    return BaselineManager(directory=tmp_path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_exists_returns_false_when_no_baseline(mgr):
    assert mgr.exists() is False


def test_save_creates_file(mgr, tmp_path):
    mgr.save(_make_snapshot())
    assert (tmp_path / "baseline.json").exists()


def test_save_writes_valid_json(mgr, tmp_path):
    mgr.save(_make_snapshot("v2"))
    raw = (tmp_path / "baseline.json").read_text()
    data = json.loads(raw)
    assert data["version"] == "v2"


def test_load_roundtrip(mgr):
    snap = _make_snapshot("v3")
    mgr.save(snap)
    loaded = mgr.load()
    assert loaded.version == "v3"
    assert len(loaded.tables) == 1
    assert loaded.tables[0].name == "users"


def test_load_raises_when_missing(mgr):
    with pytest.raises(FileNotFoundError, match="No baseline found"):
        mgr.load()


def test_exists_returns_true_after_save(mgr):
    mgr.save(_make_snapshot())
    assert mgr.exists() is True


def test_clear_removes_file(mgr):
    mgr.save(_make_snapshot())
    mgr.clear()
    assert mgr.exists() is False


def test_clear_is_idempotent(mgr):
    """Calling clear() when no baseline exists should not raise."""
    mgr.clear()  # should not raise


def test_diff_against_detects_added_column(mgr):
    base = _make_snapshot("v1")
    mgr.save(base)

    new_col = ColumnSchema(name="email", data_type="text", nullable=True)
    updated_table = TableSchema(name="users", columns=[base.tables[0].columns[0], new_col])
    updated = SchemaSnapshot(version="v2", tables=[updated_table])

    result = mgr.diff_against(updated)
    assert result.has_changes()


def test_diff_against_no_changes(mgr):
    snap = _make_snapshot("v1")
    mgr.save(snap)
    same = _make_snapshot("v1")
    result = mgr.diff_against(same)
    assert not result.has_changes()
