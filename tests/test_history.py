"""Tests for schema_drift.history.SnapshotHistory."""

import time
import pytest
from pathlib import Path

from schema_drift.history import SnapshotHistory
from schema_drift.snapshot import SchemaSnapshot, TableSchema, ColumnSchema


def _make_snapshot(version: str) -> SchemaSnapshot:
    col = ColumnSchema(name="id", data_type="INTEGER", nullable=False)
    table = TableSchema(name="users", columns=[col])
    snap = SchemaSnapshot(version=version)
    snap.tables["users"] = table
    return snap


@pytest.fixture()
def history(tmp_path: Path) -> SnapshotHistory:
    return SnapshotHistory(tmp_path / "history")


def test_save_creates_file(history: SnapshotHistory) -> None:
    snap = _make_snapshot("v1")
    path = history.save(snap)
    assert path.exists()
    assert path.suffix == ".json"


def test_load_roundtrip(history: SnapshotHistory) -> None:
    snap = _make_snapshot("v1")
    history.save(snap)
    loaded = history.load("v1")
    assert loaded.version == "v1"
    assert "users" in loaded.tables


def test_load_missing_raises(history: SnapshotHistory) -> None:
    with pytest.raises(FileNotFoundError):
        history.load("nonexistent")


def test_list_versions_empty(history: SnapshotHistory) -> None:
    assert history.list_versions() == []


def test_list_versions_ordered(history: SnapshotHistory) -> None:
    for v in ("v1", "v2", "v3"):
        history.save(_make_snapshot(v))
        time.sleep(0.01)  # ensure distinct mtimes
    versions = history.list_versions()
    assert versions == ["v1", "v2", "v3"]


def test_latest_returns_most_recent(history: SnapshotHistory) -> None:
    for v in ("v1", "v2"):
        history.save(_make_snapshot(v))
        time.sleep(0.01)
    latest = history.latest()
    assert latest is not None
    assert latest.version == "v2"


def test_latest_empty_returns_none(history: SnapshotHistory) -> None:
    assert history.latest() is None


def test_previous_returns_predecessor(history: SnapshotHistory) -> None:
    for v in ("v1", "v2", "v3"):
        history.save(_make_snapshot(v))
        time.sleep(0.01)
    prev = history.previous("v3")
    assert prev is not None
    assert prev.version == "v2"


def test_previous_first_returns_none(history: SnapshotHistory) -> None:
    history.save(_make_snapshot("v1"))
    assert history.previous("v1") is None


def test_previous_unknown_version_raises(history: SnapshotHistory) -> None:
    history.save(_make_snapshot("v1"))
    with pytest.raises(KeyError):
        history.previous("v99")


def test_history_dir_created_automatically(tmp_path: Path) -> None:
    deep = tmp_path / "a" / "b" / "history"
    h = SnapshotHistory(deep)
    assert deep.is_dir()
