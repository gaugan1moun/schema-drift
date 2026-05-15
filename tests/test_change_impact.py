"""Tests for schema_drift.change_impact."""

from __future__ import annotations

import pytest

from schema_drift.diff import DiffResult, SchemaChange, ChangeType
from schema_drift.change_impact import (
    impact_score_for,
    build_impact_report,
    ImpactReport,
    TableImpact,
)


def _change(table: str, ct: ChangeType, column: str | None = None) -> SchemaChange:
    return SchemaChange(table=table, column=column, change_type=ct, detail="")


def _diff(*changes: SchemaChange) -> DiffResult:
    return DiffResult(from_version="v1", to_version="v2", changes=list(changes))


def test_impact_score_table_removed():
    assert impact_score_for(ChangeType.TABLE_REMOVED) == 10


def test_impact_score_column_removed():
    assert impact_score_for(ChangeType.COLUMN_REMOVED) == 7


def test_impact_score_column_added():
    assert impact_score_for(ChangeType.COLUMN_ADDED) == 1


def test_build_impact_report_empty():
    report = build_impact_report(_diff())
    assert report.total_score == 0
    assert report.is_empty()
    assert report.table_impacts == []


def test_build_impact_report_versions():
    report = build_impact_report(_diff())
    assert report.from_version == "v1"
    assert report.to_version == "v2"


def test_build_impact_report_aggregates_by_table():
    diff = _diff(
        _change("orders", ChangeType.COLUMN_REMOVED, "status"),
        _change("orders", ChangeType.COLUMN_ADDED, "note"),
        _change("users", ChangeType.TABLE_REMOVED),
    )
    report = build_impact_report(diff)
    tables = {t.table: t for t in report.table_impacts}
    assert "orders" in tables
    assert "users" in tables
    assert tables["orders"].change_count == 2
    assert tables["users"].change_count == 1


def test_build_impact_report_total_score():
    diff = _diff(
        _change("orders", ChangeType.TABLE_REMOVED),
        _change("users", ChangeType.COLUMN_ADDED, "email"),
    )
    report = build_impact_report(diff)
    assert report.total_score == 10 + 1


def test_most_impacted_table_none_when_empty():
    report = build_impact_report(_diff())
    assert report.most_impacted_table() is None


def test_most_impacted_table_returns_highest():
    diff = _diff(
        _change("orders", ChangeType.TABLE_REMOVED),
        _change("users", ChangeType.COLUMN_ADDED, "x"),
    )
    report = build_impact_report(diff)
    top = report.most_impacted_table()
    assert top is not None
    assert top.table == "orders"


def test_to_dict_structure():
    diff = _diff(_change("t", ChangeType.COLUMN_ADDED, "c"))
    d = build_impact_report(diff).to_dict()
    assert "from_version" in d
    assert "to_version" in d
    assert "total_score" in d
    assert "table_impacts" in d
    assert d["table_impacts"][0]["table"] == "t"
