"""Tests for change_timeline.py."""
from datetime import datetime

import pytest

from schema_drift.change_timeline import (
    ChangeTimeline,
    TimelineEvent,
    build_timeline,
)
from schema_drift.diff import ChangeType


def _event(table="users", change_type=ChangeType.COLUMN_ADDED, column="email",
           ts=None, from_v="v1", to_v="v2"):
    return TimelineEvent(
        timestamp=ts or datetime(2024, 1, 1, 12, 0, 0),
        from_version=from_v,
        to_version=to_v,
        table=table,
        change_type=change_type,
        column=column,
    )


def test_timeline_is_empty_when_no_events():
    tl = ChangeTimeline()
    assert tl.is_empty()


def test_timeline_not_empty_with_events():
    tl = ChangeTimeline(events=[_event()])
    assert not tl.is_empty()


def test_for_table_filters_correctly():
    tl = ChangeTimeline(events=[_event(table="users"), _event(table="orders")])
    filtered = tl.for_table("users")
    assert len(filtered.events) == 1
    assert filtered.events[0].table == "users"


def test_for_change_type_filters_correctly():
    tl = ChangeTimeline(events=[
        _event(change_type=ChangeType.COLUMN_ADDED),
        _event(change_type=ChangeType.TABLE_REMOVED),
    ])
    result = tl.for_change_type(ChangeType.TABLE_REMOVED)
    assert len(result.events) == 1
    assert result.events[0].change_type == ChangeType.TABLE_REMOVED


def test_since_filters_by_date():
    tl = ChangeTimeline(events=[
        _event(ts=datetime(2024, 1, 1)),
        _event(ts=datetime(2024, 6, 1)),
    ])
    result = tl.since(datetime(2024, 3, 1))
    assert len(result.events) == 1
    assert result.events[0].timestamp == datetime(2024, 6, 1)


def test_to_dict_contains_events_key():
    tl = ChangeTimeline(events=[_event()])
    d = tl.to_dict()
    assert "events" in d
    assert len(d["events"]) == 1


def test_event_to_dict_fields():
    ev = _event()
    d = ev.to_dict()
    assert d["table"] == "users"
    assert d["change_type"] == ChangeType.COLUMN_ADDED.value
    assert d["column"] == "email"
    assert "timestamp" in d


def test_build_timeline_returns_empty_for_no_entries():
    tl = build_timeline([])
    assert tl.is_empty()
