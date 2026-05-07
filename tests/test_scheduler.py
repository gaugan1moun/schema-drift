"""Tests for schema_drift.scheduler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

import pytest

from schema_drift.diff import DiffResult, SchemaChange, ChangeType
from schema_drift.scheduler import Scheduler, SchedulerConfig
from schema_drift.watcher import SnapshotWatcher


def _make_diff(has_changes: bool = True) -> DiffResult:
    changes = []
    if has_changes:
        changes.append(
            SchemaChange(
                change_type=ChangeType.COLUMN_ADDED,
                table="users",
                column="email",
                detail="new column",
            )
        )
    return DiffResult(
        from_version="v1",
        to_version="v2",
        changes=changes,
    )


@pytest.fixture()
def mock_watcher():
    return MagicMock(spec=SnapshotWatcher)


def test_run_once_returns_none_when_watcher_returns_none(mock_watcher):
    mock_watcher.check_once.return_value = None
    scheduler = Scheduler(watcher=mock_watcher)
    result = scheduler.run_once()
    assert result is None


def test_run_once_returns_diff_when_watcher_has_diff(mock_watcher):
    diff = _make_diff()
    mock_watcher.check_once.return_value = diff
    scheduler = Scheduler(watcher=mock_watcher)
    result = scheduler.run_once()
    assert result is diff


def test_run_once_appends_to_report(mock_watcher):
    diff = _make_diff()
    mock_watcher.check_once.return_value = diff
    scheduler = Scheduler(watcher=mock_watcher)
    scheduler.run_once()
    assert len(scheduler.report.entries) == 1
    assert scheduler.report.entries[0].diff is diff


def test_run_once_calls_on_change_callback(mock_watcher):
    diff = _make_diff(has_changes=True)
    mock_watcher.check_once.return_value = diff
    callback = MagicMock()
    cfg = SchedulerConfig(on_change=callback)
    scheduler = Scheduler(watcher=mock_watcher, config=cfg)
    scheduler.run_once()
    callback.assert_called_once_with(diff)


def test_run_once_no_callback_when_no_changes(mock_watcher):
    diff = _make_diff(has_changes=False)
    mock_watcher.check_once.return_value = diff
    callback = MagicMock()
    cfg = SchedulerConfig(on_change=callback)
    scheduler = Scheduler(watcher=mock_watcher, config=cfg)
    scheduler.run_once()
    callback.assert_not_called()


def test_run_respects_max_iterations(mock_watcher):
    mock_watcher.check_once.return_value = None
    sleep_mock = MagicMock()
    cfg = SchedulerConfig(interval_seconds=5.0, max_iterations=3)
    scheduler = Scheduler(watcher=mock_watcher, config=cfg)
    scheduler.run(_sleep=sleep_mock)
    assert mock_watcher.check_once.call_count == 3
    assert sleep_mock.call_count == 2  # sleeps between iterations, not after last


def test_run_sleep_uses_configured_interval(mock_watcher):
    mock_watcher.check_once.return_value = None
    sleep_mock = MagicMock()
    cfg = SchedulerConfig(interval_seconds=42.0, max_iterations=2)
    scheduler = Scheduler(watcher=mock_watcher, config=cfg)
    scheduler.run(_sleep=sleep_mock)
    sleep_mock.assert_called_with(42.0)


def test_report_accumulates_across_multiple_run_once(mock_watcher):
    diff1 = _make_diff(has_changes=True)
    diff2 = _make_diff(has_changes=False)
    mock_watcher.check_once.side_effect = [diff1, diff2]
    scheduler = Scheduler(watcher=mock_watcher)
    scheduler.run_once()
    scheduler.run_once()
    assert len(scheduler.report.entries) == 2
