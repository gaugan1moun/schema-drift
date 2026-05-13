"""Tests for schema_drift.rollup"""
import pytest
from datetime import datetime

from schema_drift.diff import DiffResult, SchemaChange, ChangeType
from schema_drift.rollup import (
    RollupEntry,
    RollupReport,
    build_entry,
    build_rollup,
    _count_by_type,
)


def _make_diff(changes=None):
    return DiffResult(
        from_version="v1",
        to_version="v2",
        changes=changes or [],
    )


def _change(ct: ChangeType):
    return SchemaChange(table="t", column=None, change_type=ct, detail="")


NOW = datetime(2024, 6, 1)
LATER = datetime(2024, 6, 30)


def test_count_by_type_empty():
    diff = _make_diff()
    assert _count_by_type(diff, ChangeType.COLUMN_ADDED) == 0


def test_count_by_type_matches():
    diff = _make_diff([_change(ChangeType.COLUMN_ADDED), _change(ChangeType.COLUMN_ADDED)])
    assert _count_by_type(diff, ChangeType.COLUMN_ADDED) == 2


def test_build_entry_totals():
    diff = _make_diff([
        _change(ChangeType.COLUMN_ADDED),
        _change(ChangeType.COLUMN_REMOVED),
        _change(ChangeType.TABLE_ADDED),
    ])
    entry = build_entry(diff)
    assert entry.total_changes == 3
    assert entry.added_columns == 1
    assert entry.removed_columns == 1
    assert entry.added_tables == 1
    assert entry.removed_tables == 0


def test_build_entry_versions():
    diff = _make_diff()
    entry = build_entry(diff)
    assert entry.from_version == "v1"
    assert entry.to_version == "v2"


def test_build_rollup_empty():
    report = build_rollup([], NOW, LATER)
    assert report.total_changes == 0
    assert report.entries == []
    assert report.most_active_version_pair is None


def test_build_rollup_aggregates():
    d1 = _make_diff([_change(ChangeType.COLUMN_ADDED)])
    d2 = _make_diff([_change(ChangeType.COLUMN_REMOVED), _change(ChangeType.TABLE_REMOVED)])
    report = build_rollup([d1, d2], NOW, LATER)
    assert report.total_changes == 3
    assert len(report.entries) == 2


def test_most_active_version_pair():
    d1 = _make_diff([_change(ChangeType.COLUMN_ADDED)])
    d2 = _make_diff([
        _change(ChangeType.COLUMN_REMOVED),
        _change(ChangeType.COLUMN_MODIFIED),
        _change(ChangeType.TABLE_REMOVED),
    ])
    report = build_rollup([d1, d2], NOW, LATER)
    assert report.most_active_version_pair == "v1 -> v2"


def test_rollup_entry_to_dict_keys():
    entry = RollupEntry(
        from_version="v1", to_version="v2", captured_at=NOW,
        total_changes=1, added_columns=1, removed_columns=0,
        modified_columns=0, added_tables=0, removed_tables=0,
    )
    d = entry.to_dict()
    assert set(d.keys()) == {
        "from_version", "to_version", "captured_at", "total_changes",
        "added_columns", "removed_columns", "modified_columns",
        "added_tables", "removed_tables",
    }


def test_rollup_report_to_dict_structure():
    report = build_rollup([], NOW, LATER)
    d = report.to_dict()
    assert "period_start" in d
    assert "period_end" in d
    assert d["entries"] == []
