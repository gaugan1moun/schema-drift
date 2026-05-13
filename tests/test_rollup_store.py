"""Tests for schema_drift.rollup_store"""
import pytest
from datetime import datetime
from pathlib import Path

from schema_drift.diff import DiffResult, SchemaChange, ChangeType
from schema_drift.rollup import build_rollup
from schema_drift.rollup_store import RollupStore


START = datetime(2024, 6, 1)
END = datetime(2024, 6, 30)


def _make_report(tmp_path):
    return build_rollup([], START, END)


@pytest.fixture
def store(tmp_path):
    return RollupStore(tmp_path / "rollups")


def test_save_creates_file(store, tmp_path):
    report = _make_report(tmp_path)
    path = store.save(report)
    assert path.exists()


def test_save_filename_contains_date(store, tmp_path):
    report = _make_report(tmp_path)
    path = store.save(report)
    assert "20240601" in path.name


def test_load_roundtrip(store, tmp_path):
    report = _make_report(tmp_path)
    store.save(report)
    loaded = store.load(START)
    assert loaded.period_start == START
    assert loaded.period_end == END
    assert loaded.entries == []


def test_load_missing_raises(store):
    with pytest.raises(FileNotFoundError):
        store.load(datetime(2000, 1, 1))


def test_list_reports_empty(store):
    assert store.list_reports() == []


def test_list_reports_returns_saved(store, tmp_path):
    r1 = build_rollup([], datetime(2024, 1, 1), datetime(2024, 1, 31))
    r2 = build_rollup([], datetime(2024, 2, 1), datetime(2024, 2, 28))
    store.save(r1)
    store.save(r2)
    reports = store.list_reports()
    assert len(reports) == 2


def test_list_reports_sorted(store, tmp_path):
    r1 = build_rollup([], datetime(2024, 3, 1), datetime(2024, 3, 31))
    r2 = build_rollup([], datetime(2024, 1, 1), datetime(2024, 1, 31))
    store.save(r1)
    store.save(r2)
    reports = store.list_reports()
    assert reports[0].period_start < reports[1].period_start


def test_store_creates_directory(tmp_path):
    nested = tmp_path / "a" / "b" / "rollups"
    s = RollupStore(nested)
    assert nested.exists()
