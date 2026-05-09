"""Tests for schema_drift.annotator."""

import pytest
from pathlib import Path

from schema_drift.annotator import Annotation, AnnotationStore


@pytest.fixture
def store(tmp_path: Path) -> AnnotationStore:
    return AnnotationStore(path=tmp_path / "annotations.json")


def _ann(table="users", column="email", note="reviewed", author="alice") -> Annotation:
    return Annotation(table=table, column=column, note=note, author=author)


# --- Annotation dataclass ---

def test_annotation_to_dict_fields():
    a = _ann()
    d = a.to_dict()
    assert d["table"] == "users"
    assert d["column"] == "email"
    assert d["note"] == "reviewed"
    assert d["author"] == "alice"


def test_annotation_from_dict_roundtrip():
    a = _ann()
    restored = Annotation.from_dict(a.to_dict())
    assert restored.table == a.table
    assert restored.column == a.column
    assert restored.note == a.note
    assert restored.author == a.author


def test_annotation_from_dict_defaults():
    a = Annotation.from_dict({"table": "t", "note": "n"})
    assert a.column is None
    assert a.author == "unknown"


# --- AnnotationStore ---

def test_store_starts_empty(store):
    assert store.all() == []


def test_add_persists(store, tmp_path):
    store.add(_ann())
    reloaded = AnnotationStore(path=tmp_path / "annotations.json")
    assert len(reloaded.all()) == 1


def test_get_by_table_and_column(store):
    store.add(_ann(table="users", column="email"))
    store.add(_ann(table="users", column="name"))
    store.add(_ann(table="orders", column="id"))
    results = store.get("users", "email")
    assert len(results) == 1
    assert results[0].column == "email"


def test_get_table_level_annotation(store):
    store.add(Annotation(table="users", column=None, note="deprecated"))
    results = store.get("users", None)
    assert len(results) == 1
    assert results[0].note == "deprecated"


def test_get_returns_empty_for_unknown(store):
    assert store.get("nonexistent", "col") == []


def test_remove_returns_count(store):
    store.add(_ann(table="users", column="email"))
    store.add(_ann(table="users", column="email", note="second note"))
    removed = store.remove("users", "email")
    assert removed == 2


def test_remove_leaves_others_intact(store):
    store.add(_ann(table="users", column="email"))
    store.add(_ann(table="orders", column="id"))
    store.remove("users", "email")
    assert len(store.all()) == 1
    assert store.all()[0].table == "orders"


def test_file_created_on_add(store, tmp_path):
    store.add(_ann())
    assert (tmp_path / "annotations.json").exists()
