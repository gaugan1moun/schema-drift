"""Tests for schema_drift.change_streak."""
from datetime import date
from typing import List

import pytest

from schema_drift.change_streak import ChangeStreak, StreakPoint, build_streak
from schema_drift.rollup import RollupEntry


def _entry(period: str, total: int) -> RollupEntry:
    return RollupEntry(
        period=period,
        from_version="v1",
        to_version="v2",
        total_changes=total,
        count_by_type={},
    )


@pytest.fixture()
def consecutive_entries() -> List[RollupEntry]:
    return [
        _entry("2024-01-01", 3),
        _entry("2024-01-02", 5),
        _entry("2024-01-03", 2),
        _entry("2024-01-04", 0),
        _entry("2024-01-05", 1),
    ]


def test_build_streak_empty():
    result = build_streak([])
    assert result.is_empty()
    assert result.current_streak == 0
    assert result.longest_streak == 0


def test_build_streak_point_count(consecutive_entries):
    result = build_streak(consecutive_entries)
    assert len(result.points) == len(consecutive_entries)


def test_build_streak_point_periods(consecutive_entries):
    result = build_streak(consecutive_entries)
    periods = [p.period for p in result.points]
    assert periods == ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04", "2024-01-05"]


def test_build_streak_longest_streak(consecutive_entries):
    result = build_streak(consecutive_entries)
    # First three days are consecutive active days
    assert result.longest_streak == 3


def test_build_streak_longest_streak_bounds(consecutive_entries):
    result = build_streak(consecutive_entries)
    assert result.longest_streak_start == "2024-01-01"
    assert result.longest_streak_end == "2024-01-03"


def test_build_streak_current_streak(consecutive_entries):
    result = build_streak(consecutive_entries)
    # Last active day is 2024-01-05, standalone streak of 1
    assert result.current_streak == 1


def test_build_streak_all_active():
    entries = [_entry(f"2024-02-0{i}", i) for i in range(1, 6)]
    result = build_streak(entries)
    assert result.longest_streak == 5
    assert result.current_streak == 5


def test_build_streak_no_active_days():
    entries = [_entry("2024-03-01", 0), _entry("2024-03-02", 0)]
    result = build_streak(entries)
    assert result.longest_streak == 0
    assert result.current_streak == 0
    assert result.longest_streak_start is None


def test_streak_point_to_dict():
    p = StreakPoint(period="2024-04-01", total_changes=7)
    d = p.to_dict()
    assert d["period"] == "2024-04-01"
    assert d["total_changes"] == 7


def test_streak_to_dict_keys():
    result = build_streak([_entry("2024-05-01", 4)])
    d = result.to_dict()
    assert "current_streak" in d
    assert "longest_streak" in d
    assert "longest_streak_start" in d
    assert "longest_streak_end" in d
    assert "points" in d


def test_build_streak_respects_window_days():
    # Gap of 2 days; with window_days=2 they should form a streak
    entries = [_entry("2024-06-01", 2), _entry("2024-06-03", 3)]
    result = build_streak(entries, window_days=2)
    assert result.longest_streak == 2
