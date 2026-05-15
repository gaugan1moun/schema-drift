"""Tests for change_blame and blame_report modules."""
import json
import pytest

from schema_drift.diff import DiffResult, SchemaChange, ChangeType
from schema_drift.change_blame import (
    BlameRule,
    BlamedChange,
    BlameReport,
    build_blame_report,
    _resolve_owner,
)
from schema_drift import blame_report as br


def _change(table: str, ct: ChangeType = ChangeType.COLUMN_ADDED, col: str = "col") -> SchemaChange:
    return SchemaChange(table=table, change_type=ct, column=col)


def _diff(*changes: SchemaChange) -> DiffResult:
    return DiffResult(from_version="v1", to_version="v2", changes=list(changes))


@pytest.fixture
def rules():
    return [
        BlameRule(table_pattern="orders*", owner="payments-team"),
        BlameRule(table_pattern="users", owner="identity-team"),
    ]


def test_blame_rule_matches_exact():
    rule = BlameRule(table_pattern="users", owner="identity-team")
    assert rule.matches("users") is True


def test_blame_rule_matches_wildcard():
    rule = BlameRule(table_pattern="orders*", owner="payments-team")
    assert rule.matches("orders_archive") is True


def test_blame_rule_no_match():
    rule = BlameRule(table_pattern="users", owner="identity-team")
    assert rule.matches("products") is False


def test_resolve_owner_first_match(rules):
    assert _resolve_owner("orders_items", rules) == "payments-team"


def test_resolve_owner_no_match(rules):
    assert _resolve_owner("products", rules) is None


def test_build_blame_report_assigns_owner(rules):
    diff = _diff(_change("users"), _change("orders_items"))
    report = build_blame_report(diff, rules)
    owners = {bc.change.table: bc.owner for bc in report.blamed}
    assert owners["users"] == "identity-team"
    assert owners["orders_items"] == "payments-team"


def test_build_blame_report_unowned(rules):
    diff = _diff(_change("products"))
    report = build_blame_report(diff, rules)
    assert report.blamed[0].owner is None


def test_blame_report_is_empty_when_no_changes(rules):
    diff = _diff()
    report = build_blame_report(diff, rules)
    assert report.is_empty() is True


def test_by_owner_groups_correctly(rules):
    diff = _diff(_change("users"), _change("orders"), _change("products"))
    report = build_blame_report(diff, rules)
    grouped = report.by_owner()
    assert "identity-team" in grouped
    assert "payments-team" in grouped
    assert "unowned" in grouped


def test_to_dict_structure(rules):
    diff = _diff(_change("users"))
    report = build_blame_report(diff, rules)
    d = report.to_dict()
    assert d["from_version"] == "v1"
    assert d["to_version"] == "v2"
    assert isinstance(d["blamed"], list)
    assert d["blamed"][0]["owner"] == "identity-team"


def test_render_text_no_changes(rules):
    diff = _diff()
    report = build_blame_report(diff, rules)
    out = br.render_text(report)
    assert "No changes" in out


def test_render_text_shows_owner(rules):
    diff = _diff(_change("users"))
    report = build_blame_report(diff, rules)
    out = br.render_text(report)
    assert "identity-team" in out
    assert "users" in out


def test_render_markdown_table_format(rules):
    diff = _diff(_change("orders"))
    report = build_blame_report(diff, rules)
    out = br.render_markdown(report)
    assert "|" in out
    assert "payments-team" in out


def test_render_json_valid(rules):
    diff = _diff(_change("users"))
    report = build_blame_report(diff, rules)
    out = br.render_json(report)
    data = json.loads(out)
    assert data["from_version"] == "v1"


def test_render_dispatch(rules):
    diff = _diff(_change("users"))
    report = build_blame_report(diff, rules)
    assert br.render(report, fmt="json") == br.render_json(report)
    assert br.render(report, fmt="markdown") == br.render_markdown(report)
    assert br.render(report, fmt="text") == br.render_text(report)
