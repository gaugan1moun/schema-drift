"""Tests for change_suppression and suppression_store."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from schema_drift.diff import ChangeType, SchemaChange, DiffResult
from schema_drift.change_suppression import (
    SuppressionRule,
    apply_suppressions,
    suppression_summary,
)
from schema_drift.suppression_store import SuppressionStore


def _change(
    table: str = "orders",
    column: str | None = "status",
    change_type: ChangeType = ChangeType.COLUMN_REMOVED,
) -> SchemaChange:
    return SchemaChange(
        change_type=change_type,
        table_name=table,
        column_name=column,
    )


def _diff(*changes: SchemaChange) -> DiffResult:
    return DiffResult(
        from_version="v1",
        to_version="v2",
        changes=list(changes),
    )


# --- SuppressionRule.matches ---

def test_rule_matches_exact_table_and_column():
    rule = SuppressionRule(table_pattern="orders", column_pattern="status")
    assert rule.matches(_change("orders", "status")) is True


def test_rule_no_match_wrong_table():
    rule = SuppressionRule(table_pattern="users", column_pattern="*")
    assert rule.matches(_change("orders", "status")) is False


def test_rule_matches_wildcard_table():
    rule = SuppressionRule(table_pattern="order*", column_pattern="*")
    assert rule.matches(_change("orders_archive", "id")) is True


def test_rule_filters_by_change_type():
    rule = SuppressionRule(
        table_pattern="*",
        column_pattern="*",
        change_types=[ChangeType.TABLE_ADDED],
    )
    assert rule.matches(_change(change_type=ChangeType.COLUMN_REMOVED)) is False
    assert rule.matches(_change(change_type=ChangeType.TABLE_ADDED, column=None)) is True


def test_rule_matches_no_column_change():
    rule = SuppressionRule(table_pattern="orders", column_pattern="*")
    change = _change("orders", None, ChangeType.TABLE_REMOVED)
    assert rule.matches(change) is True


# --- apply_suppressions ---

def test_apply_suppressions_no_rules():
    diff = _diff(_change(), _change("users", "email"))
    result = apply_suppressions(diff, [])
    assert len(result.retained) == 2
    assert len(result.suppressed) == 0


def test_apply_suppressions_suppresses_matching():
    rule = SuppressionRule(table_pattern="orders", column_pattern="*")
    diff = _diff(_change("orders", "status"), _change("users", "email"))
    result = apply_suppressions(diff, [rule])
    assert result.suppression_count == 1
    assert result.retained[0].table_name == "users"


def test_apply_suppressions_all_suppressed():
    rule = SuppressionRule(table_pattern="*", column_pattern="*")
    diff = _diff(_change(), _change())
    result = apply_suppressions(diff, [rule])
    assert result.has_retained_changes is False
    assert result.suppression_count == 2


def test_suppression_summary_text():
    rule = SuppressionRule(table_pattern="orders", column_pattern="*")
    diff = _diff(_change("orders", "x"), _change("users", "y"))
    result = apply_suppressions(diff, [rule])
    summary = suppression_summary(result)
    assert "2 total" in summary
    assert "1 suppressed" in summary
    assert "1 retained" in summary


# --- SuppressionStore ---

@pytest.fixture
def store(tmp_path: Path) -> SuppressionStore:
    return SuppressionStore(tmp_path / "suppressions" / "rules.json")


def test_exists_false_before_save(store: SuppressionStore):
    assert store.exists() is False


def test_save_creates_file(store: SuppressionStore):
    store.save([])
    assert store.exists() is True


def test_save_and_load_roundtrip(store: SuppressionStore):
    rules = [
        SuppressionRule(
            table_pattern="orders",
            column_pattern="status",
            change_types=[ChangeType.COLUMN_REMOVED],
            reason="known migration",
        )
    ]
    store.save(rules)
    loaded = store.load()
    assert len(loaded) == 1
    assert loaded[0].table_pattern == "orders"
    assert loaded[0].reason == "known migration"
    assert ChangeType.COLUMN_REMOVED in loaded[0].change_types


def test_load_missing_raises(store: SuppressionStore):
    with pytest.raises(FileNotFoundError):
        store.load()


def test_save_empty_rules_produces_valid_json(store: SuppressionStore, tmp_path: Path):
    store.save([])
    raw = (tmp_path / "suppressions" / "rules.json").read_text()
    assert json.loads(raw) == []
