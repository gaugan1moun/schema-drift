"""Tests for schema_drift.policy and schema_drift.policy_loader."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from schema_drift.diff import ChangeType, DiffResult, SchemaChange
from schema_drift.policy import PolicyRule, evaluate_policy
from schema_drift.policy_loader import load_rules, rule_from_dict, rule_to_dict, save_rules


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _change(change_type: ChangeType, table: str = "orders", column: str = "price") -> SchemaChange:
    return SchemaChange(change_type=change_type, table=table, column=column)


def _diff(*changes: SchemaChange) -> DiffResult:
    return DiffResult(from_version="v1", to_version="v2", changes=list(changes))


# ---------------------------------------------------------------------------
# PolicyRule.check
# ---------------------------------------------------------------------------

def test_check_returns_block_for_blocked_type():
    rule = PolicyRule(name="no-drops", blocked_change_types=[ChangeType.COLUMN_REMOVED])
    change = _change(ChangeType.COLUMN_REMOVED)
    assert rule.check(change) == "block"


def test_check_returns_warn_for_warn_type():
    rule = PolicyRule(name="warn-type", warn_change_types=[ChangeType.TYPE_CHANGED])
    change = _change(ChangeType.TYPE_CHANGED)
    assert rule.check(change) == "warn"


def test_check_returns_none_for_unrelated_change():
    rule = PolicyRule(name="no-drops", blocked_change_types=[ChangeType.COLUMN_REMOVED])
    change = _change(ChangeType.COLUMN_ADDED)
    assert rule.check(change) is None


def test_check_blocks_removal_on_blocked_table():
    rule = PolicyRule(name="protect-users", blocked_tables=["users"])
    change = _change(ChangeType.COLUMN_REMOVED, table="users")
    assert rule.check(change) == "block"


# ---------------------------------------------------------------------------
# evaluate_policy
# ---------------------------------------------------------------------------

def test_evaluate_no_violations():
    rule = PolicyRule(name="no-drops", blocked_change_types=[ChangeType.COLUMN_REMOVED])
    diff = _diff(_change(ChangeType.COLUMN_ADDED))
    result = evaluate_policy([rule], diff)
    assert not result.is_blocked
    assert result.violations == []


def test_evaluate_detects_block():
    rule = PolicyRule(name="no-drops", blocked_change_types=[ChangeType.COLUMN_REMOVED])
    diff = _diff(_change(ChangeType.COLUMN_REMOVED))
    result = evaluate_policy([rule], diff)
    assert result.is_blocked
    assert len(result.blocks) == 1


def test_evaluate_detects_warn():
    rule = PolicyRule(name="warn-type", warn_change_types=[ChangeType.TYPE_CHANGED])
    diff = _diff(_change(ChangeType.TYPE_CHANGED))
    result = evaluate_policy([rule], diff)
    assert not result.is_blocked
    assert len(result.warnings) == 1


def test_evaluate_multiple_rules_and_changes():
    rules = [
        PolicyRule(name="no-drops", blocked_change_types=[ChangeType.COLUMN_REMOVED]),
        PolicyRule(name="warn-type", warn_change_types=[ChangeType.TYPE_CHANGED]),
    ]
    diff = _diff(_change(ChangeType.COLUMN_REMOVED), _change(ChangeType.TYPE_CHANGED))
    result = evaluate_policy(rules, diff)
    assert result.is_blocked
    assert len(result.warnings) == 1
    assert len(result.blocks) == 1


# ---------------------------------------------------------------------------
# policy_loader
# ---------------------------------------------------------------------------

def test_rule_from_dict_fields():
    data = {
        "name": "no-drops",
        "description": "No column drops allowed",
        "blocked_change_types": ["column_removed"],
        "blocked_tables": ["payments"],
        "warn_change_types": ["type_changed"],
    }
    rule = rule_from_dict(data)
    assert rule.name == "no-drops"
    assert ChangeType.COLUMN_REMOVED in rule.blocked_change_types
    assert "payments" in rule.blocked_tables
    assert ChangeType.TYPE_CHANGED in rule.warn_change_types


def test_rule_to_dict_roundtrip():
    rule = PolicyRule(
        name="no-drops",
        blocked_change_types=[ChangeType.COLUMN_REMOVED],
        warn_change_types=[ChangeType.TYPE_CHANGED],
    )
    assert rule_from_dict(rule_to_dict(rule)).name == rule.name


def test_save_and_load_rules(tmp_path: Path):
    rules = [
        PolicyRule(name="r1", blocked_change_types=[ChangeType.TABLE_REMOVED]),
        PolicyRule(name="r2", warn_change_types=[ChangeType.COLUMN_ADDED]),
    ]
    dest = tmp_path / "policies.json"
    save_rules(rules, dest)
    loaded = load_rules(dest)
    assert len(loaded) == 2
    assert loaded[0].name == "r1"
    assert ChangeType.TABLE_REMOVED in loaded[0].blocked_change_types


def test_save_creates_parent_dirs(tmp_path: Path):
    dest = tmp_path / "nested" / "dir" / "rules.json"
    save_rules([], dest)
    assert dest.exists()
