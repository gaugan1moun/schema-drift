"""Tests for change_heatmap and heatmap_report modules."""
import json
import pytest

from schema_drift.rollup import RollupEntry
from schema_drift.change_heatmap import build_heatmap, ChangeHeatmap, HeatmapCell
from schema_drift.heatmap_report import render_text, render_markdown, render_json, render


def _make_entry(from_v: str, to_v: str, changes_by_table: dict) -> RollupEntry:
    total = sum(sum(v.values()) for v in changes_by_table.values())
    return RollupEntry(
        from_version=from_v,
        to_version=to_v,
        total_changes=total,
        changes_by_table=changes_by_table,
        count_by_type={},
    )


@pytest.fixture
def entries():
    return [
        _make_entry("v1", "v2", {"users": {"COLUMN_ADDED": 2}, "orders": {"COLUMN_REMOVED": 1}}),
        _make_entry("v2", "v3", {"users": {"COLUMN_MODIFIED": 1}, "products": {"TABLE_ADDED": 1}}),
    ]


def test_build_heatmap_tables(entries):
    hm = build_heatmap(entries)
    assert "users" in hm.tables
    assert "orders" in hm.tables
    assert "products" in hm.tables


def test_build_heatmap_periods(entries):
    hm = build_heatmap(entries)
    assert "v2" in hm.periods
    assert "v3" in hm.periods


def test_build_heatmap_cell_values(entries):
    hm = build_heatmap(entries)
    assert hm.get("users", "v2") == 2
    assert hm.get("users", "v3") == 1
    assert hm.get("orders", "v2") == 1
    assert hm.get("orders", "v3") == 0
    assert hm.get("products", "v3") == 1


def test_build_heatmap_empty():
    hm = build_heatmap([])
    assert hm.is_empty()
    assert hm.tables == []
    assert hm.periods == []


def test_hottest_cell(entries):
    hm = build_heatmap(entries)
    hot = hm.hottest_cell()
    assert hot is not None
    assert hot.table == "users"
    assert hot.period == "v2"
    assert hot.change_count == 2


def test_hottest_cell_empty():
    hm = ChangeHeatmap()
    assert hm.hottest_cell() is None


def test_to_dict(entries):
    hm = build_heatmap(entries)
    d = hm.to_dict()
    assert "periods" in d
    assert "tables" in d
    assert "cells" in d
    assert isinstance(d["cells"], list)


def test_render_text_empty():
    hm = ChangeHeatmap()
    out = render_text(hm)
    assert "No schema changes" in out


def test_render_text_with_data(entries):
    hm = build_heatmap(entries)
    out = render_text(hm)
    assert "users" in out
    assert "Hottest cell" in out


def test_render_markdown_with_data(entries):
    hm = build_heatmap(entries)
    out = render_markdown(hm)
    assert "##" in out
    assert "|" in out
    assert "users" in out


def test_render_json_valid(entries):
    hm = build_heatmap(entries)
    out = render_json(hm)
    data = json.loads(out)
    assert "cells" in data


def test_render_dispatch(entries):
    hm = build_heatmap(entries)
    assert render(hm, "text") == render_text(hm)
    assert render(hm, "markdown") == render_markdown(hm)
    assert render(hm, "json") == render_json(hm)
