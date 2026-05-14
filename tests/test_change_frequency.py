"""Tests for schema_drift.change_frequency."""
from __future__ import annotations

import pytest

from schema_drift.change_frequency import (
    ChangeFrequencyReport,
    TableFrequency,
    build_frequency_report,
)
from schema_drift.rollup import RollupEntry, RollupReport


def _make_entry(
    from_v: str,
    to_v: str,
    changes_by_table: dict,
    total: int = 0,
) -> RollupEntry:
    return RollupEntry(
        from_version=from_v,
        to_version=to_v,
        total_changes=total or sum(changes_by_table.values()),
        changes_by_type={},
        changes_by_table=changes_by_table,
    )


@pytest.fixture()
def single_report() -> RollupReport:
    entries = [
        _make_entry("v1", "v2", {"users": 3, "orders": 1}),
        _make_entry("v2", "v3", {"users": 2, "products": 5}),
    ]
    return RollupReport(entries=entries)


@pytest.fixture()
def two_reports() -> list:
    r1 = RollupReport(
        entries=[_make_entry("v1", "v2", {"users": 3, "orders": 1})]
    )
    r2 = RollupReport(
        entries=[_make_entry("v2", "v3", {"users": 2, "orders": 4})]
    )
    return [r1, r2]


def test_build_frequency_report_empty():
    result = build_frequency_report([])
    assert result.table_frequencies == []


def test_build_frequency_aggregates_tables(single_report):
    result = build_frequency_report([single_report])
    tables = {tf.table: tf.change_count for tf in result.table_frequencies}
    assert tables["users"] == 5
    assert tables["orders"] == 1
    assert tables["products"] == 5


def test_build_frequency_versions_seen(single_report):
    result = build_frequency_report([single_report])
    users_tf = next(tf for tf in result.table_frequencies if tf.table == "users")
    assert users_tf.versions_seen == 2


def test_build_frequency_across_multiple_reports(two_reports):
    result = build_frequency_report(two_reports)
    tables = {tf.table: tf.change_count for tf in result.table_frequencies}
    assert tables["users"] == 5
    assert tables["orders"] == 5


def test_most_changed_table(single_report):
    result = build_frequency_report([single_report])
    most = result.most_changed_table()
    assert most is not None
    assert most.table in ("users", "products")
    assert most.change_count == 5


def test_least_changed_table(single_report):
    result = build_frequency_report([single_report])
    least = result.least_changed_table()
    assert least is not None
    assert least.change_count == 1


def test_sorted_by_frequency_descending(single_report):
    result = build_frequency_report([single_report])
    sorted_list = result.sorted_by_frequency(descending=True)
    counts = [tf.change_count for tf in sorted_list]
    assert counts == sorted(counts, reverse=True)


def test_sorted_by_frequency_ascending(single_report):
    result = build_frequency_report([single_report])
    sorted_list = result.sorted_by_frequency(descending=False)
    counts = [tf.change_count for tf in sorted_list]
    assert counts == sorted(counts)


def test_most_changed_table_empty():
    report = ChangeFrequencyReport(table_frequencies=[])
    assert report.most_changed_table() is None
    assert report.least_changed_table() is None


def test_to_dict_structure(single_report):
    result = build_frequency_report([single_report])
    d = result.to_dict()
    assert "table_frequencies" in d
    assert all("table" in tf for tf in d["table_frequencies"])
    assert all("change_count" in tf for tf in d["table_frequencies"])
    assert all("versions_seen" in tf for tf in d["table_frequencies"])
