"""Tests for schema_drift.tag_store module."""
import json
import pytest
from pathlib import Path

from schema_drift.tag_store import TagStore


@pytest.fixture()
def store(tmp_path):
    return TagStore(tmp_path)


def test_get_tags_missing_version(store):
    assert store.get_tags("v1") == []


def test_set_tags_persists(tmp_path):
    s = TagStore(tmp_path)
    s.set_tags("v1", ["prod", "reviewed"])
    s2 = TagStore(tmp_path)
    assert s2.get_tags("v1") == ["prod", "reviewed"]


def test_add_tag(store):
    store.add_tag("v1", "prod")
    assert "prod" in store.get_tags("v1")


def test_add_tag_no_duplicate(store):
    store.add_tag("v1", "prod")
    store.add_tag("v1", "prod")
    assert store.get_tags("v1").count("prod") == 1


def test_remove_tag(store):
    store.set_tags("v1", ["prod", "staging"])
    store.remove_tag("v1", "staging")
    assert store.get_tags("v1") == ["prod"]


def test_remove_tag_nonexistent_does_not_raise(store):
    store.set_tags("v1", ["prod"])
    store.remove_tag("v1", "ghost")
    assert store.get_tags("v1") == ["prod"]


def test_all_versions(store):
    store.set_tags("v1", ["prod"])
    store.set_tags("v2", ["staging"])
    assert set(store.all_versions()) == {"v1", "v2"}


def test_versions_with_tag(store):
    store.set_tags("v1", ["prod", "reviewed"])
    store.set_tags("v2", ["staging"])
    store.set_tags("v3", ["prod"])
    assert set(store.versions_with_tag("prod")) == {"v1", "v3"}


def test_creates_parent_dirs(tmp_path):
    nested = tmp_path / "a" / "b"
    s = TagStore(nested)
    s.set_tags("v1", ["x"])
    assert (nested / "tags.json").exists()


def test_json_file_structure(tmp_path):
    s = TagStore(tmp_path)
    s.set_tags("v1", ["prod"])
    data = json.loads((tmp_path / "tags.json").read_text())
    assert data == {"v1": ["prod"]}
