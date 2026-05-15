"""Tests for schema_drift.change_forecast."""
import pytest

from schema_drift.change_forecast import (
    ForecastPoint,
    ChangeForecast,
    build_forecast,
    _moving_average,
)
from schema_drift.rollup import RollupEntry


def _make_entry(total: int, label: str = "v1..v2") -> RollupEntry:
    from datetime import date
    return RollupEntry(
        from_version="v1",
        to_version="v2",
        date=date.today().isoformat(),
        total_changes=total,
        count_by_type={},
    )


# ---------------------------------------------------------------------------
# _moving_average
# ---------------------------------------------------------------------------

def test_moving_average_single_value():
    assert _moving_average([10.0], 3) == [10.0]


def test_moving_average_window_larger_than_series():
    result = _moving_average([2.0, 4.0], 5)
    assert result[0] == pytest.approx(2.0)
    assert result[1] == pytest.approx(3.0)


def test_moving_average_exact_window():
    result = _moving_average([1.0, 3.0, 5.0], 3)
    assert result[-1] == pytest.approx(3.0)


# ---------------------------------------------------------------------------
# build_forecast
# ---------------------------------------------------------------------------

def test_build_forecast_empty_returns_empty():
    fc = build_forecast([])
    assert fc.is_empty()


def test_build_forecast_point_count_matches_horizon():
    entries = [_make_entry(t) for t in [4, 6, 8, 10]]
    fc = build_forecast(entries, horizon=3)
    assert len(fc.points) == 3


def test_build_forecast_predicted_value_is_moving_average():
    entries = [_make_entry(t) for t in [10, 10, 10, 10]]
    fc = build_forecast(entries, horizon=2, window_size=4)
    for p in fc.points:
        assert p.predicted_changes == pytest.approx(10.0)


def test_build_forecast_confidence_decreases():
    entries = [_make_entry(t) for t in [5, 5, 5]]
    fc = build_forecast(entries, horizon=3)
    confs = [p.confidence for p in fc.points]
    assert confs[0] > confs[1] > confs[2]


def test_build_forecast_confidence_never_negative():
    entries = [_make_entry(t) for t in [1, 2, 3]]
    fc = build_forecast(entries, horizon=10)
    for p in fc.points:
        assert p.confidence >= 0.0


def test_build_forecast_next_predicted_returns_first_point():
    entries = [_make_entry(t) for t in [3, 6]]
    fc = build_forecast(entries, horizon=2)
    assert fc.next_predicted() == fc.points[0]


def test_build_forecast_period_labels():
    entries = [_make_entry(t) for t in [2, 4]]
    fc = build_forecast(entries, horizon=2)
    assert fc.points[0].period == "forecast+1"
    assert fc.points[1].period == "forecast+2"


def test_build_forecast_to_dict_structure():
    entries = [_make_entry(t) for t in [5, 10]]
    fc = build_forecast(entries, horizon=1)
    d = fc.to_dict()
    assert "window_size" in d
    assert "points" in d
    assert isinstance(d["points"], list)
