"""Tests for schema_drift.change_anomaly."""
import pytest

from schema_drift.change_anomaly import (
    AnomalyPoint,
    AnomalyReport,
    build_anomaly_report,
)
from schema_drift.rollup import RollupEntry


def _make_entry(period: str, total: int) -> RollupEntry:
    return RollupEntry(
        period=period,
        from_version="v1",
        to_version="v2",
        total_changes=total,
        count_by_type={},
    )


@pytest.fixture
def uniform_entries():
    return [_make_entry(f"2024-0{i}", 10) for i in range(1, 6)]


@pytest.fixture
def spike_entries():
    return [
        _make_entry("2024-01", 5),
        _make_entry("2024-02", 6),
        _make_entry("2024-03", 5),
        _make_entry("2024-04", 50),  # spike
        _make_entry("2024-05", 6),
    ]


def test_build_anomaly_report_empty():
    report = build_anomaly_report([])
    assert report.is_empty()
    assert report.anomalies() == []
    assert report.worst() is None


def test_build_anomaly_report_point_count(uniform_entries):
    report = build_anomaly_report(uniform_entries)
    assert len(report.points) == 5


def test_build_anomaly_report_periods(spike_entries):
    report = build_anomaly_report(spike_entries)
    periods = [p.period for p in report.points]
    assert periods == ["2024-01", "2024-02", "2024-03", "2024-04", "2024-05"]


def test_uniform_data_no_anomalies(uniform_entries):
    report = build_anomaly_report(uniform_entries, threshold=2.0)
    assert report.anomalies() == []


def test_spike_detected(spike_entries):
    report = build_anomaly_report(spike_entries, threshold=2.0)
    anomalies = report.anomalies()
    assert len(anomalies) == 1
    assert anomalies[0].period == "2024-04"


def test_worst_returns_highest_z_score(spike_entries):
    report = build_anomaly_report(spike_entries)
    worst = report.worst()
    assert worst is not None
    assert worst.period == "2024-04"


def test_z_scores_are_floats(spike_entries):
    report = build_anomaly_report(spike_entries)
    for point in report.points:
        assert isinstance(point.z_score, float)


def test_single_entry_no_std_dev():
    entries = [_make_entry("2024-01", 20)]
    report = build_anomaly_report(entries)
    assert len(report.points) == 1
    assert report.points[0].z_score == 0.0
    assert report.points[0].std_dev == 0.0


def test_to_dict_structure(spike_entries):
    report = build_anomaly_report(spike_entries)
    d = report.to_dict()
    assert "threshold" in d
    assert "points" in d
    assert "anomalies" in d
    assert isinstance(d["points"], list)


def test_anomaly_point_to_dict_fields(spike_entries):
    report = build_anomaly_report(spike_entries)
    d = report.points[0].to_dict()
    assert set(d.keys()) == {"period", "total_changes", "mean", "std_dev", "z_score"}
