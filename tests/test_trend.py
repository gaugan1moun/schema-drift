"""Tests for schema_drift.trend."""
import pytest
from schema_drift.trend import TrendPoint, TrendReport, build_trend
from schema_drift.rollup import RollupEntry


def _make_entry(from_v: str, to_v: str, counts: dict) -> RollupEntry:
    total = sum(counts.values())
    return RollupEntry(
        from_version=from_v,
        to_version=to_v,
        total_changes=total,
        count_by_type=counts,
        affected_tables=[],
    )


@pytest.fixture
def entries():
    return [
        _make_entry("v1", "v2", {"TABLE_ADDED": 1, "COLUMN_REMOVED": 2}),
        _make_entry("v2", "v3", {"COLUMN_TYPE_CHANGED": 3}),
        _make_entry("v3", "v4", {"TABLE_REMOVED": 5, "COLUMN_ADDED": 1}),
    ]


def test_build_trend_returns_correct_point_count(entries):
    report = build_trend(entries)
    assert len(report.points) == 3


def test_build_trend_labels(entries):
    report = build_trend(entries)
    assert report.points[0].label == "v1 -> v2"
    assert report.points[2].label == "v3 -> v4"


def test_build_trend_total_changes(entries):
    report = build_trend(entries)
    assert report.points[0].total_changes == 3
    assert report.points[1].total_changes == 3
    assert report.points[2].total_changes == 6


def test_build_trend_high_severity(entries):
    report = build_trend(entries)
    # v1->v2: COLUMN_REMOVED=2 => high=2
    assert report.points[0].high_severity == 2
    # v3->v4: TABLE_REMOVED=5 => high=5
    assert report.points[2].high_severity == 5


def test_build_trend_medium_severity(entries):
    report = build_trend(entries)
    # v2->v3: COLUMN_TYPE_CHANGED=3
    assert report.points[1].medium_severity == 3


def test_peak_returns_highest(entries):
    report = build_trend(entries)
    assert report.peak().label == "v3 -> v4"


def test_average_changes(entries):
    report = build_trend(entries)
    assert report.average_changes() == pytest.approx((3 + 3 + 6) / 3)


def test_is_increasing_true(entries):
    report = build_trend(entries)
    assert report.is_increasing() is True


def test_is_increasing_false():
    entries = [
        _make_entry("v1", "v2", {"TABLE_REMOVED": 10}),
        _make_entry("v2", "v3", {"COLUMN_ADDED": 1}),
    ]
    report = build_trend(entries)
    assert report.is_increasing() is False


def test_empty_trend():
    report = build_trend([])
    assert report.is_empty
    assert report.peak() is None
    assert report.average_changes() == 0.0
    assert report.is_increasing() is False


def test_to_dict_structure(entries):
    report = build_trend(entries)
    d = report.to_dict()
    assert "points" in d
    assert "average_changes" in d
    assert "peak_label" in d
    assert d["peak_label"] == "v3 -> v4"
    assert d["is_increasing"] is True


def test_trend_point_to_dict():
    p = TrendPoint(label="v1 -> v2", total_changes=4, high_severity=1,
                   medium_severity=2, low_severity=1)
    d = p.to_dict()
    assert d["label"] == "v1 -> v2"
    assert d["total_changes"] == 4
