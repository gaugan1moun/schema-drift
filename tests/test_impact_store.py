"""Tests for schema_drift.impact_store."""

from __future__ import annotations

import pytest

from schema_drift.change_impact import ImpactReport, TableImpact, build_impact_report
from schema_drift.diff import DiffResult, SchemaChange, ChangeType
from schema_drift.impact_store import ImpactStore


def _make_report(from_v: str = "v1", to_v: str = "v2", score: int = 5) -> ImpactReport:
    return ImpactReport(
        from_version=from_v,
        to_version=to_v,
        total_score=score,
        table_impacts=[
            TableImpact(table="orders", score=score, change_count=1)
        ],
    )


@pytest.fixture()
def store(tmp_path):
    return ImpactStore(tmp_path / "impacts")


def test_save_creates_file(store, tmp_path):
    report = _make_report()
    p = store.save(report)
    assert p.exists()


def test_load_roundtrip(store):
    report = _make_report()
    store.save(report)
    loaded = store.load("v1", "v2")
    assert loaded.from_version == "v1"
    assert loaded.to_version == "v2"
    assert loaded.total_score == 5
    assert loaded.table_impacts[0].table == "orders"


def test_load_missing_raises(store):
    with pytest.raises(FileNotFoundError):
        store.load("x", "y")


def test_exists_false_before_save(store):
    assert not store.exists("v1", "v2")


def test_exists_true_after_save(store):
    store.save(_make_report())
    assert store.exists("v1", "v2")


def test_list_reports_empty(store):
    assert store.list_reports() == []


def test_list_reports_returns_all(store):
    store.save(_make_report("v1", "v2"))
    store.save(_make_report("v2", "v3", score=3))
    reports = store.list_reports()
    assert len(reports) == 2


def test_list_reports_versions(store):
    store.save(_make_report("v1", "v2"))
    store.save(_make_report("v2", "v3"))
    pairs = {(r.from_version, r.to_version) for r in store.list_reports()}
    assert ("v1", "v2") in pairs
    assert ("v2", "v3") in pairs
