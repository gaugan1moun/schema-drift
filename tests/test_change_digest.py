"""Tests for change_digest and digest_report."""
from __future__ import annotations

import json
from datetime import date

import pytest

from schema_drift.change_digest import build_digest, ChangeDigest, DigestEntry
from schema_drift.digest_report import render_text, render_markdown, render_json, render
from schema_drift.rollup import RollupEntry


def _entry(from_date: str, total: int, types: dict, tables=None) -> RollupEntry:
    return RollupEntry(
        from_version=from_date,
        to_version=from_date,
        total=total,
        count_by_type=types,
        tables_affected=tables or ["users"],
    )


@pytest.fixture
def entries():
    return [
        _entry("2024-01-01", 3, {"COLUMN_ADDED": 2, "TABLE_ADDED": 1}, ["users", "orders"]),
        _entry("2024-01-04", 1, {"COLUMN_REMOVED": 1}, ["products"]),
        _entry("2024-01-09", 5, {"TABLE_REMOVED": 2, "COLUMN_ADDED": 3}, ["logs"]),
    ]


def test_build_digest_empty():
    result = build_digest([])
    assert result.is_empty()


def test_build_digest_returns_digest(entries):
    result = build_digest(entries, window_days=7, reference_date=date(2024, 1, 15))
    assert isinstance(result, ChangeDigest)
    assert not result.is_empty()


def test_build_digest_groups_by_window(entries):
    result = build_digest(entries, window_days=7, reference_date=date(2024, 1, 15))
    # entries on 1-01 and 1-04 fall in same 7-day window from 2024-01-01
    totals = [e.total_changes for e in result.entries]
    assert sum(totals) == 9  # 3 + 1 + 5


def test_build_digest_tables_affected(entries):
    result = build_digest(entries, window_days=7, reference_date=date(2024, 1, 15))
    # At least one window should report multiple tables
    max_tables = max(e.tables_affected for e in result.entries)
    assert max_tables >= 2


def test_build_digest_type_counts(entries):
    result = build_digest(entries, window_days=30, reference_date=date(2024, 1, 15))
    # All entries in one window
    assert len(result.entries) == 1
    types = result.entries[0].top_change_types
    assert types.get("COLUMN_ADDED", 0) == 5
    assert types.get("TABLE_REMOVED", 0) == 2


def test_latest_returns_last_entry(entries):
    result = build_digest(entries, window_days=7, reference_date=date(2024, 1, 15))
    latest = result.latest()
    assert latest is not None
    assert isinstance(latest, DigestEntry)


def test_total_changes_sums_all(entries):
    result = build_digest(entries, window_days=30, reference_date=date(2024, 1, 15))
    assert result.total_changes() == 9


def test_to_dict_structure(entries):
    result = build_digest(entries, window_days=30, reference_date=date(2024, 1, 15))
    d = result.to_dict()
    assert "entries" in d
    assert isinstance(d["entries"], list)


def test_render_text_empty():
    out = render_text(ChangeDigest())
    assert "No digest" in out


def test_render_text_contains_period(entries):
    result = build_digest(entries, window_days=30, reference_date=date(2024, 1, 15))
    out = render_text(result)
    assert "2024-01" in out
    assert "Total changes" in out


def test_render_markdown_contains_heading(entries):
    result = build_digest(entries, window_days=30, reference_date=date(2024, 1, 15))
    out = render_markdown(result)
    assert "##" in out
    assert "window" in out


def test_render_json_valid(entries):
    result = build_digest(entries, window_days=30, reference_date=date(2024, 1, 15))
    out = render_json(result)
    parsed = json.loads(out)
    assert "entries" in parsed


def test_render_dispatch(entries):
    result = build_digest(entries, window_days=30, reference_date=date(2024, 1, 15))
    assert render(result, "text") == render_text(result)
    assert render(result, "markdown") == render_markdown(result)
    assert render(result, "json") == render_json(result)
