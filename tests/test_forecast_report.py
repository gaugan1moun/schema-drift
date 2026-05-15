"""Tests for schema_drift.forecast_report."""
import json

import pytest

from schema_drift.change_forecast import build_forecast, ChangeForecast
from schema_drift.forecast_report import render_text, render_markdown, render_json, render
from schema_drift.rollup import RollupEntry
from datetime import date


def _entry(total: int) -> RollupEntry:
    return RollupEntry(
        from_version="a",
        to_version="b",
        date=date.today().isoformat(),
        total_changes=total,
        count_by_type={},
    )


@pytest.fixture
def empty_forecast() -> ChangeForecast:
    return build_forecast([])


@pytest.fixture
def rich_forecast() -> ChangeForecast:
    return build_forecast([_entry(t) for t in [4, 8, 6, 10]], horizon=3)


def test_text_empty_message(empty_forecast):
    out = render_text(empty_forecast)
    assert "No historical data" in out


def test_text_contains_header(rich_forecast):
    out = render_text(rich_forecast)
    assert "Schema Change Forecast" in out


def test_text_contains_period_labels(rich_forecast):
    out = render_text(rich_forecast)
    assert "forecast+1" in out
    assert "forecast+2" in out


def test_text_contains_window_size(rich_forecast):
    out = render_text(rich_forecast)
    assert str(rich_forecast.window_size) in out


def test_markdown_empty_message(empty_forecast):
    out = render_markdown(empty_forecast)
    assert "No historical data" in out


def test_markdown_contains_table(rich_forecast):
    out = render_markdown(rich_forecast)
    assert "|" in out
    assert "forecast+1" in out


def test_json_is_valid(rich_forecast):
    out = render_json(rich_forecast)
    data = json.loads(out)
    assert "points" in data
    assert len(data["points"]) == 3


def test_render_dispatches_text(rich_forecast):
    assert render(rich_forecast, fmt="text") == render_text(rich_forecast)


def test_render_dispatches_markdown(rich_forecast):
    assert render(rich_forecast, fmt="markdown") == render_markdown(rich_forecast)


def test_render_dispatches_json(rich_forecast):
    assert render(rich_forecast, fmt="json") == render_json(rich_forecast)


def test_render_defaults_to_text(rich_forecast):
    assert render(rich_forecast) == render_text(rich_forecast)
