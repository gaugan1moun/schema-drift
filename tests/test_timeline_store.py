"""Tests for timeline_store.py."""
from datetime import datetime
from pathlib import Path

import pytest

from schema_drift.change_timeline import ChangeTimeline, TimelineEvent
from schema_drift.diff import ChangeType
from schema_drift.timeline_store import TimelineStore


def _event(table="users", ts=None):
    return TimelineEvent(
        timestamp=ts or datetime(2024, 1, 15, 10, 0, 0),
        from_version="v1",
        to_version="v2",
        table=table,
        change_type=ChangeType.COLUMN_ADDED,
        column="name",
    )


@pytest.fixture
def store(tmp_path):
    return TimelineStore(tmp_path / "timeline_data")


def test_exists_false_before_save(store):
    assert not store.exists()


def test_save_creates_file(store, tmp_path):
    tl = ChangeTimeline(events=[_event()])
    store.save(tl)
    assert store.exists()


def test_load_roundtrip(store):
    tl = ChangeTimeline(events=[_event()])
    store.save(tl)
    loaded = store.load()
    assert len(loaded.events) == 1
    assert loaded.events[0].table == "users"
    assert loaded.events[0].change_type == ChangeType.COLUMN_ADDED


def test_load_missing_raises(store):
    with pytest.raises(FileNotFoundError):
        store.load()


def test_load_preserves_timestamp(store):
    ts = datetime(2024, 3, 22, 8, 30, 0)
    tl = ChangeTimeline(events=[_event(ts=ts)])
    store.save(tl)
    loaded = store.load()
    assert loaded.events[0].timestamp == ts


def test_append_merges_events(store):
    tl1 = ChangeTimeline(events=[_event(table="users", ts=datetime(2024, 1, 1))])
    tl2 = ChangeTimeline(events=[_event(table="orders", ts=datetime(2024, 2, 1))])
    store.save(tl1)
    store.append(tl2)
    loaded = store.load()
    assert len(loaded.events) == 2


def test_append_deduplicates_events(store):
    ev = _event()
    tl = ChangeTimeline(events=[ev])
    store.save(tl)
    store.append(ChangeTimeline(events=[ev]))
    loaded = store.load()
    assert len(loaded.events) == 1
