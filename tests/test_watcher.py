"""Tests for schema_drift.watcher."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from schema_drift.snapshot import SchemaSnapshot, TableSchema, ColumnSchema
from schema_drift.serializer import dump
from schema_drift.watcher import SnapshotWatcher


def _write_snapshot(path: Path, snapshot: SchemaSnapshot) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        dump(snapshot, fh)


def _make_snapshot(version: str, with_extra_table: bool = False) -> SchemaSnapshot:
    col = ColumnSchema(name="id", data_type="integer", nullable=False)
    table = TableSchema(name="users", columns=[col])
    tables = {"users": table}
    if with_extra_table:
        col2 = ColumnSchema(name="name", data_type="text", nullable=True)
        tables["orders"] = TableSchema(name="orders", columns=[col2])
    return SchemaSnapshot(version=version, tables=tables)


@pytest.fixture()
def snapshot_file(tmp_path: Path) -> Path:
    return tmp_path / "snapshot.json"


def test_check_once_no_file_returns_none(snapshot_file: Path) -> None:
    watcher = SnapshotWatcher(snapshot_file, on_change=lambda d: None)
    assert watcher.check_once() is None


def test_check_once_first_load_sets_baseline(snapshot_file: Path) -> None:
    _write_snapshot(snapshot_file, _make_snapshot("v1"))
    watcher = SnapshotWatcher(snapshot_file, on_change=lambda d: None)
    result = watcher.check_once()
    # First load — no previous snapshot to diff against
    assert result is None
    assert watcher._last_snapshot is not None
    assert watcher._last_snapshot.version == "v1"


def test_check_once_no_change_returns_none(snapshot_file: Path) -> None:
    _write_snapshot(snapshot_file, _make_snapshot("v1"))
    watcher = SnapshotWatcher(snapshot_file, on_change=lambda d: None)
    watcher.check_once()  # baseline
    result = watcher.check_once()  # same mtime
    assert result is None


def test_check_once_detects_change(snapshot_file: Path, tmp_path: Path) -> None:
    _write_snapshot(snapshot_file, _make_snapshot("v1"))
    watcher = SnapshotWatcher(snapshot_file, on_change=lambda d: None)
    watcher.check_once()  # baseline

    # Overwrite with a different snapshot (force new mtime)
    time.sleep(0.05)
    _write_snapshot(snapshot_file, _make_snapshot("v2", with_extra_table=True))
    # Manually bump mtime so the watcher sees it as changed
    watcher._last_mtime = 0.0

    received: list = []
    watcher.on_change = received.append
    result = watcher.check_once()

    assert result is not None
    assert result.has_changes()
    assert len(received) == 1


def test_watch_respects_max_iterations(snapshot_file: Path) -> None:
    _write_snapshot(snapshot_file, _make_snapshot("v1"))
    watcher = SnapshotWatcher(snapshot_file, on_change=lambda d: None, poll_interval=0)
    # Should complete without hanging
    watcher.watch(max_iterations=3)
    assert watcher._last_snapshot is not None
