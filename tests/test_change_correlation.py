"""Tests for change_correlation module."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock
from datetime import datetime, timezone

from schema_drift.change_correlation import (
    CorrelationPair,
    CorrelationReport,
    build_correlation_report,
)
from schema_drift.audit import AuditEntry, AuditReport
from schema_drift.diff import DiffResult, SchemaChange, ChangeType


def _make_change(table: str, change_type: ChangeType = ChangeType.COLUMN_ADDED) -> SchemaChange:
    return SchemaChange(change_type=change_type, table=table, column="col")


def _make_diff(*tables: str) -> DiffResult:
    diff = MagicMock(spec=DiffResult)
    diff.changes = [_make_change(t) for t in tables]
    diff.has_changes.return_value = bool(tables)
    diff.from_version = "v1"
    diff.to_version = "v2"
    return diff


def _make_entry(diff: DiffResult) -> AuditEntry:
    entry = MagicMock(spec=AuditEntry)
    entry.diff = diff
    entry.has_changes.return_value = diff.has_changes()
    return entry


@pytest.fixture
def report_two_entries() -> AuditReport:
    d1 = _make_diff("users", "orders")
    d2 = _make_diff("users", "orders")
    report = MagicMock(spec=AuditReport)
    report.entries = [_make_entry(d1), _make_entry(d2)]
    return report


@pytest.fixture
def report_no_changes() -> AuditReport:
    diff = _make_diff()
    report = MagicMock(spec=AuditReport)
    report.entries = [_make_entry(diff)]
    return report


def test_build_correlation_empty_report():
    report = MagicMock(spec=AuditReport)
    report.entries = []
    result = build_correlation_report(report)
    assert result.is_empty()
    assert result.total_versions_analyzed == 0


def test_build_correlation_no_changes(report_no_changes):
    result = build_correlation_report(report_no_changes)
    assert result.is_empty()


def test_build_correlation_pair_count(report_two_entries):
    result = build_correlation_report(report_two_entries)
    assert len(result.pairs) == 1


def test_build_correlation_co_change_count(report_two_entries):
    result = build_correlation_report(report_two_entries)
    pair = result.pairs[0]
    assert pair.co_change_count == 2


def test_build_correlation_ratio(report_two_entries):
    result = build_correlation_report(report_two_entries)
    pair = result.pairs[0]
    assert pair.correlation_ratio == 1.0


def test_build_correlation_total_versions(report_two_entries):
    result = build_correlation_report(report_two_entries)
    assert result.total_versions_analyzed == 2


def test_top_pairs_returns_sorted():
    p1 = CorrelationPair("a", "b", co_change_count=1, total_versions=10)
    p2 = CorrelationPair("c", "d", co_change_count=7, total_versions=10)
    p3 = CorrelationPair("e", "f", co_change_count=4, total_versions=10)
    report = CorrelationReport(pairs=[p1, p2, p3], total_versions_analyzed=10)
    top = report.top_pairs(2)
    assert top[0].table_a == "c"
    assert top[1].table_a == "e"


def test_correlation_pair_to_dict():
    pair = CorrelationPair("users", "orders", co_change_count=3, total_versions=5)
    d = pair.to_dict()
    assert d["table_a"] == "users"
    assert d["table_b"] == "orders"
    assert d["co_change_count"] == 3
    assert d["correlation_ratio"] == 0.6


def test_report_to_dict_keys(report_two_entries):
    result = build_correlation_report(report_two_entries)
    d = result.to_dict()
    assert "total_versions_analyzed" in d
    assert "pairs" in d
