"""Tests for change_velocity and velocity_report modules."""
from __future__ import annotations

import json
from datetime import datetime

import pytest

from schema_drift.change_velocity import (
    VelocityPoint,
    VelocityReport,
    build_velocity_report,
)
from schema_drift.velocity_report import render, render_json, render_markdown, render_text


def _entry(from_ver: str, total: int, tables: list[str]):
    """Minimal RollupEntry-like object."""
    from schema_drift.rollup import RollupEntry
    from schema_drift.diff import ChangeType
    return RollupEntry(
        from_version=from_ver,
        to_version=from_ver + "_next",
        total_changes=total,
        tables_affected=tables,
        count_by_type={ChangeType.COLUMN_ADDED: total},
    )


@pytest.fixture
def entries():
    return [
        _entry("2024-01-01", 5, ["users", "orders"]),
        _entry("2024-01-04", 3, ["orders"]),
        _entry("2024-01-10", 8, ["products", "users"]),
        _entry("2024-01-15", 2, ["products"]),
    ]


def test_build_velocity_report_empty():
    report = build_velocity_report([])
    assert report.is_empty()
    assert report.average_changes() == 0.0
    assert report.peak() is None


def test_build_velocity_report_returns_points(entries):
    report = build_velocity_report(entries, window_days=7)
    assert not report.is_empty()
    assert len(report.points) > 0


def test_build_velocity_report_window_days_stored(entries):
    report = build_velocity_report(entries, window_days=14)
    assert report.window_days == 14


def test_build_velocity_aggregates_changes(entries):
    report = build_velocity_report(entries, window_days=7)
    total = sum(p.change_count for p in report.points)
    assert total == 18  # 5+3+8+2


def test_peak_returns_highest_window(entries):
    report = build_velocity_report(entries, window_days=7)
    peak = report.peak()
    assert peak is not None
    assert peak.change_count == max(p.change_count for p in report.points)


def test_average_changes_is_float(entries):
    report = build_velocity_report(entries, window_days=7)
    avg = report.average_changes()
    assert isinstance(avg, float)
    assert avg > 0


def test_velocity_point_to_dict():
    pt = VelocityPoint(
        window_start=datetime(2024, 1, 1),
        window_end=datetime(2024, 1, 8),
        change_count=5,
        tables_affected=2,
    )
    d = pt.to_dict()
    assert d["change_count"] == 5
    assert d["tables_affected"] == 2
    assert "window_start" in d


def test_velocity_report_to_dict(entries):
    report = build_velocity_report(entries, window_days=7)
    d = report.to_dict()
    assert "points" in d
    assert d["window_days"] == 7
    assert "average_changes" in d


def test_render_text_no_data():
    report = VelocityReport(window_days=7)
    out = render_text(report)
    assert "No data" in out


def test_render_text_with_data(entries):
    report = build_velocity_report(entries, window_days=7)
    out = render_text(report)
    assert "Average" in out
    assert "Peak" in out


def test_render_markdown_table(entries):
    report = build_velocity_report(entries, window_days=7)
    out = render_markdown(report)
    assert "|" in out
    assert "Window Start" in out


def test_render_json_valid(entries):
    report = build_velocity_report(entries, window_days=7)
    out = render_json(report)
    parsed = json.loads(out)
    assert parsed["window_days"] == 7
    assert isinstance(parsed["points"], list)


def test_render_dispatches_format(entries):
    report = build_velocity_report(entries, window_days=7)
    assert render(report, fmt="text") == render_text(report)
    assert render(report, fmt="markdown") == render_markdown(report)
    assert render(report, fmt="json") == render_json(report)
