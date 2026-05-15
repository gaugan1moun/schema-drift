"""Tests for correlation_report rendering."""
from __future__ import annotations

import json
import pytest

from schema_drift.change_correlation import CorrelationPair, CorrelationReport
from schema_drift.correlation_report import render_text, render_markdown, render_json, render


@pytest.fixture
def empty_report() -> CorrelationReport:
    return CorrelationReport(pairs=[], total_versions_analyzed=3)


@pytest.fixture
def rich_report() -> CorrelationReport:
    pairs = [
        CorrelationPair("users", "orders", co_change_count=4, total_versions=5),
        CorrelationPair("products", "inventory", co_change_count=2, total_versions=5),
    ]
    return CorrelationReport(pairs=pairs, total_versions_analyzed=5)


def test_text_empty_message(empty_report):
    out = render_text(empty_report)
    assert "No co-changing" in out


def test_text_versions_analyzed(rich_report):
    out = render_text(rich_report)
    assert "5 versions analyzed" in out


def test_text_shows_pair(rich_report):
    out = render_text(rich_report)
    assert "users" in out
    assert "orders" in out


def test_text_shows_ratio(rich_report):
    out = render_text(rich_report)
    assert "80.00%" in out


def test_markdown_empty_message(empty_report):
    out = render_markdown(empty_report)
    assert "_No co-changing" in out


def test_markdown_has_table_header(rich_report):
    out = render_markdown(rich_report)
    assert "| Table A |" in out


def test_markdown_shows_pair(rich_report):
    out = render_markdown(rich_report)
    assert "users" in out
    assert "orders" in out


def test_json_valid(rich_report):
    out = render_json(rich_report)
    data = json.loads(out)
    assert "pairs" in data
    assert data["total_versions_analyzed"] == 5


def test_json_pair_fields(rich_report):
    out = render_json(rich_report)
    data = json.loads(out)
    pair = data["pairs"][0]
    assert "table_a" in pair
    assert "correlation_ratio" in pair


def test_render_delegates_text(rich_report):
    assert render(rich_report, fmt="text") == render_text(rich_report)


def test_render_delegates_markdown(rich_report):
    assert render(rich_report, fmt="markdown") == render_markdown(rich_report)


def test_render_delegates_json(rich_report):
    assert render(rich_report, fmt="json") == render_json(rich_report)
