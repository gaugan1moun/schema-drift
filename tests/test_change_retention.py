"""Tests for change_retention, retention_store, and retention_report."""
from __future__ import annotations

import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from schema_drift.change_retention import (
    RetentionPolicy,
    RetentionResult,
    apply_retention,
)
from schema_drift.retention_store import RetentionStore
from schema_drift.retention_report import render_text, render_markdown, render_json
from schema_drift.rollup import RollupEntry


def _make_entry(version_from: str, version_to: str, total: int, days_ago: int = 0) -> RollupEntry:
    period = (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
    return RollupEntry(
        version_from=version_from,
        version_to=version_to,
        period=period,
        total_changes=total,
        count_by_type={},
    )


# --- apply_retention tests ---

def test_apply_retention_no_policy_keeps_all():
    entries = [_make_entry("v1", "v2", 3), _make_entry("v2", "v3", 0)]
    policy = RetentionPolicy()
    result = apply_retention(entries, policy)
    assert result.kept_count == 2
    assert result.pruned_count == 0


def test_apply_retention_max_entries_prunes_oldest():
    entries = [
        _make_entry("v1", "v2", 1, days_ago=10),
        _make_entry("v2", "v3", 2, days_ago=5),
        _make_entry("v3", "v4", 3, days_ago=1),
    ]
    policy = RetentionPolicy(max_entries=2, keep_versions_with_changes=False)
    result = apply_retention(entries, policy)
    assert result.kept_count == 2
    assert result.pruned_count == 1


def test_apply_retention_max_age_prunes_old_entries():
    entries = [
        _make_entry("v1", "v2", 0, days_ago=30),
        _make_entry("v2", "v3", 0, days_ago=2),
    ]
    policy = RetentionPolicy(max_age_days=10, keep_versions_with_changes=False)
    result = apply_retention(entries, policy)
    assert result.kept_count == 1
    assert result.pruned_count == 1


def test_apply_retention_keeps_changed_entries_even_if_old():
    entries = [
        _make_entry("v1", "v2", 5, days_ago=60),
        _make_entry("v2", "v3", 0, days_ago=60),
    ]
    policy = RetentionPolicy(max_age_days=10, keep_versions_with_changes=True)
    result = apply_retention(entries, policy)
    # v1->v2 has changes, should be kept; v2->v3 has none, pruned
    kept_pairs = [(e.version_from, e.version_to) for e in result.kept]
    assert ("v1", "v2") in kept_pairs
    assert result.pruned_count == 1


def test_retention_result_to_dict_structure():
    entries = [_make_entry("v1", "v2", 1)]
    policy = RetentionPolicy(max_entries=1)
    result = apply_retention(entries, policy)
    d = result.to_dict()
    assert "kept_count" in d
    assert "pruned_count" in d
    assert "kept_versions" in d
    assert "pruned_versions" in d


# --- RetentionStore tests ---

@pytest.fixture
def store(tmp_path):
    return RetentionStore(tmp_path)


def test_store_exists_false_before_save(store):
    assert not store.exists()


def test_store_save_creates_file(store, tmp_path):
    policy = RetentionPolicy(max_entries=10, max_age_days=30)
    store.save(policy)
    assert (tmp_path / "retention_policy.json").exists()


def test_store_load_roundtrip(store):
    policy = RetentionPolicy(max_entries=5, max_age_days=14, keep_versions_with_changes=False)
    store.save(policy)
    loaded = store.load()
    assert loaded.max_entries == 5
    assert loaded.max_age_days == 14
    assert loaded.keep_versions_with_changes is False


def test_store_load_missing_raises(store):
    with pytest.raises(FileNotFoundError):
        store.load()


def test_store_delete_removes_file(store):
    store.save(RetentionPolicy(max_entries=3))
    store.delete()
    assert not store.exists()


# --- retention_report tests ---

@pytest.fixture
def sample_result():
    kept = [_make_entry("v2", "v3", 2)]
    pruned = [_make_entry("v1", "v2", 0)]
    r = RetentionResult(kept=kept, pruned=pruned)
    return r


def test_render_text_contains_header(sample_result):
    out = render_text(sample_result)
    assert "Retention Report" in out


def test_render_text_shows_counts(sample_result):
    out = render_text(sample_result)
    assert "1" in out


def test_render_markdown_contains_table(sample_result):
    out = render_markdown(sample_result)
    assert "|" in out


def test_render_json_valid(sample_result):
    out = render_json(sample_result)
    data = json.loads(out)
    assert data["kept_count"] == 1
    assert data["pruned_count"] == 1
