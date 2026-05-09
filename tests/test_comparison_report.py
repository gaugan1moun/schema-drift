"""Tests for schema_drift.comparison_report."""

import json
import pytest
from datetime import datetime, timezone

from schema_drift.snapshot import SchemaSnapshot, TableSchema, ColumnSchema
from schema_drift.comparator import compare
from schema_drift.comparison_report import render_text, render_markdown, render_json, render


def _col(name, dtype="TEXT", nullable=True):
    return ColumnSchema(name=name, data_type=dtype, nullable=nullable)


def _snap(version, tables):
    return SchemaSnapshot(
        version=version,
        captured_at=datetime.now(timezone.utc),
        tables={t.name: t for t in tables},
    )


@pytest.fixture
def no_change_result():
    snap = _snap("v1", [TableSchema(name="users", columns={"id": _col("id", "INT")})])
    return compare(snap, snap)


@pytest.fixture
def change_result():
    base = _snap("v1", [
        TableSchema(name="users", columns={"id": _col("id", "INT"), "name": _col("name")}),
        TableSchema(name="logs", columns={"id": _col("id", "INT")}),
    ])
    updated = _snap("v2", [
        TableSchema(name="users", columns={"id": _col("id", "BIGINT"), "name": _col("name")}),
    ])
    return compare(base, updated)


def test_text_no_changes_message(no_change_result):
    out = render_text(no_change_result)
    assert "No schema changes" in out


def test_text_includes_versions(change_result):
    out = render_text(change_result)
    assert "v1" in out and "v2" in out


def test_text_includes_severity_label(change_result):
    out = render_text(change_result)
    assert "HIGH" in out or "MEDIUM" in out


def test_markdown_contains_table_header(change_result):
    out = render_markdown(change_result)
    assert "| Severity |" in out


def test_markdown_no_changes_italic(no_change_result):
    out = render_markdown(no_change_result)
    assert "_No schema changes detected._" in out


def test_json_is_valid(change_result):
    out = render_json(change_result)
    data = json.loads(out)
    assert "changes" in data
    assert "summary" in data


def test_json_summary_keys(change_result):
    data = json.loads(render_json(change_result))
    assert set(data["summary"]) == {"high", "medium", "low"}


def test_render_dispatch_text(change_result):
    assert render(change_result, "text") == render_text(change_result)


def test_render_dispatch_markdown(change_result):
    assert render(change_result, "markdown") == render_markdown(change_result)


def test_render_dispatch_json(change_result):
    assert render(change_result, "json") == render_json(change_result)


def test_render_unknown_format_raises(change_result):
    with pytest.raises(ValueError, match="Unknown format"):
        render(change_result, "xml")
