"""Tests for schema_drift.tags module."""
import pytest
from datetime import datetime

from schema_drift.snapshot import SchemaSnapshot
from schema_drift.tags import (
    TaggedSnapshot,
    TagIndex,
    filter_by_tag,
    filter_by_any_tag,
)


def _make_snapshot(version: str) -> SchemaSnapshot:
    return SchemaSnapshot(version=version, captured_at=datetime.utcnow(), tables={})


@pytest.fixture()
def tagged_list():
    ts1 = TaggedSnapshot(snapshot=_make_snapshot("v1"), tags=["prod", "reviewed"])
    ts2 = TaggedSnapshot(snapshot=_make_snapshot("v2"), tags=["staging"])
    ts3 = TaggedSnapshot(snapshot=_make_snapshot("v3"), tags=["prod"])
    return [ts1, ts2, ts3]


def test_has_tag_true():
    ts = TaggedSnapshot(snapshot=_make_snapshot("v1"), tags=["prod"])
    assert ts.has_tag("prod") is True


def test_has_tag_false():
    ts = TaggedSnapshot(snapshot=_make_snapshot("v1"), tags=["prod"])
    assert ts.has_tag("staging") is False


def test_add_tag_no_duplicate():
    ts = TaggedSnapshot(snapshot=_make_snapshot("v1"), tags=["prod"])
    ts.add_tag("prod")
    assert ts.tags.count("prod") == 1


def test_remove_tag():
    ts = TaggedSnapshot(snapshot=_make_snapshot("v1"), tags=["prod", "staging"])
    ts.remove_tag("staging")
    assert "staging" not in ts.tags
    assert "prod" in ts.tags


def test_filter_by_tag(tagged_list):
    result = filter_by_tag(tagged_list, "prod")
    versions = [ts.snapshot.version for ts in result]
    assert versions == ["v1", "v3"]


def test_filter_by_any_tag(tagged_list):
    result = filter_by_any_tag(tagged_list, ["staging", "reviewed"])
    versions = {ts.snapshot.version for ts in result}
    assert versions == {"v1", "v2"}


def test_tag_index_register_and_versions_for_tag(tagged_list):
    idx = TagIndex()
    for ts in tagged_list:
        idx.register(ts)
    assert set(idx.versions_for_tag("prod")) == {"v1", "v3"}


def test_tag_index_tags_for_version(tagged_list):
    idx = TagIndex()
    for ts in tagged_list:
        idx.register(ts)
    assert set(idx.tags_for_version("v1")) == {"prod", "reviewed"}


def test_tag_index_all_tags(tagged_list):
    idx = TagIndex()
    for ts in tagged_list:
        idx.register(ts)
    assert set(idx.all_tags()) == {"prod", "reviewed", "staging"}
