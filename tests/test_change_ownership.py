"""Tests for change_ownership, ownership_report, and ownership_store."""
from __future__ import annotations

import json
import pytest

from schema_drift.diff import ChangeType, SchemaChange, DiffResult
from schema_drift.change_ownership import OwnershipRule, assign_ownership
from schema_drift.ownership_report import render_text, render_markdown, render_json
from schema_drift.ownership_store import OwnershipStore


def _change(table: str, column: str | None, ct: ChangeType) -> SchemaChange:
    return SchemaChange(table=table, column=column, change_type=ct)


def _diff(*changes: SchemaChange) -> DiffResult:
    from schema_drift.diff import DiffResult
    return DiffResult(from_version="v1", to_version="v2", changes=list(changes))


# ---------------------------------------------------------------------------
# OwnershipRule.matches
# ---------------------------------------------------------------------------

def test_rule_matches_exact_table():
    rule = OwnershipRule(owner="team-a", table_pattern="orders")
    change = _change("orders", None, ChangeType.TABLE_ADDED)
    assert rule.matches(change)


def test_rule_no_match_wrong_table():
    rule = OwnershipRule(owner="team-a", table_pattern="orders")
    change = _change("users", None, ChangeType.TABLE_ADDED)
    assert not rule.matches(change)


def test_rule_matches_wildcard_table():
    rule = OwnershipRule(owner="team-b", table_pattern="order*")
    assert rule.matches(_change("orders", None, ChangeType.TABLE_REMOVED))
    assert rule.matches(_change("order_items", None, ChangeType.TABLE_REMOVED))


def test_rule_matches_column_pattern():
    rule = OwnershipRule(owner="dba", table_pattern="*", column_pattern="id")
    assert rule.matches(_change("users", "id", ChangeType.COLUMN_REMOVED))
    assert not rule.matches(_change("users", "email", ChangeType.COLUMN_REMOVED))


# ---------------------------------------------------------------------------
# assign_ownership
# ---------------------------------------------------------------------------

def test_assign_ownership_owned():
    rules = [OwnershipRule(owner="team-a", table_pattern="orders")]
    diff = _diff(_change("orders", None, ChangeType.TABLE_ADDED))
    report = assign_ownership(diff, rules)
    assert len(report.owned) == 1
    assert report.owned[0].owner == "team-a"
    assert len(report.unowned) == 0


def test_assign_ownership_unowned():
    rules = [OwnershipRule(owner="team-a", table_pattern="orders")]
    diff = _diff(_change("users", None, ChangeType.TABLE_ADDED))
    report = assign_ownership(diff, rules)
    assert len(report.unowned) == 1
    assert len(report.owned) == 0


def test_assign_ownership_first_rule_wins():
    rules = [
        OwnershipRule(owner="first", table_pattern="orders"),
        OwnershipRule(owner="second", table_pattern="orders"),
    ]
    diff = _diff(_change("orders", None, ChangeType.TABLE_ADDED))
    report = assign_ownership(diff, rules)
    assert report.owned[0].owner == "first"


def test_assign_ownership_empty_diff():
    report = assign_ownership(_diff(), [])
    assert report.is_empty()


# ---------------------------------------------------------------------------
# ownership_report rendering
# ---------------------------------------------------------------------------

def test_render_text_contains_owner():
    rules = [OwnershipRule(owner="team-a", table_pattern="orders")]
    diff = _diff(_change("orders", None, ChangeType.TABLE_ADDED))
    report = assign_ownership(diff, rules)
    out = render_text(report)
    assert "team-a" in out
    assert "orders" in out


def test_render_markdown_contains_owner():
    rules = [OwnershipRule(owner="team-a", table_pattern="orders")]
    diff = _diff(_change("orders", None, ChangeType.TABLE_ADDED))
    report = assign_ownership(diff, rules)
    out = render_markdown(report)
    assert "team-a" in out


def test_render_json_is_valid():
    rules = [OwnershipRule(owner="team-a", table_pattern="orders")]
    diff = _diff(_change("orders", "id", ChangeType.COLUMN_REMOVED))
    report = assign_ownership(diff, rules)
    data = json.loads(render_json(report))
    assert data["from_version"] == "v1"
    assert len(data["owned"]) == 1


# ---------------------------------------------------------------------------
# OwnershipStore
# ---------------------------------------------------------------------------

@pytest.fixture()
def store(tmp_path):
    return OwnershipStore(tmp_path / "ownership.json")


def test_store_exists_false_before_save(store):
    assert not store.exists()


def test_store_save_creates_file(store):
    store.save([OwnershipRule(owner="team-a", table_pattern="orders")])
    assert store.exists()


def test_store_load_roundtrip(store):
    rules = [
        OwnershipRule(owner="team-a", table_pattern="orders", column_pattern="*"),
        OwnershipRule(owner="team-b", table_pattern="users", column_pattern="email"),
    ]
    store.save(rules)
    loaded = store.load()
    assert len(loaded) == 2
    assert loaded[0].owner == "team-a"
    assert loaded[1].column_pattern == "email"


def test_store_load_missing_raises(store):
    with pytest.raises(FileNotFoundError):
        store.load()
