"""Tests for schema_drift.classification_report."""
import json
import pytest
from schema_drift.diff import ChangeType, SchemaChange, DiffResult
from schema_drift.change_classifier import classify
from schema_drift.classification_report import render_text, render_markdown, render_json, render


def _diff(*change_types) -> DiffResult:
    changes = [
        SchemaChange(change_type=ct, table="tbl", column="col" if "COLUMN" in ct.value else None, detail="")
        for ct in change_types
    ]
    return DiffResult(from_version="v1", to_version="v2", changes=changes)


@pytest.fixture
def empty_result():
    return classify(_diff())


@pytest.fixture
def rich_result():
    return classify(_diff(
        ChangeType.TABLE_REMOVED,
        ChangeType.COLUMN_ADDED,
        ChangeType.COLUMN_NULLABLE_CHANGED,
    ))


def test_text_empty_result(empty_result):
    text = render_text(empty_result)
    assert "No changes detected" in text
    assert "none" in text.lower()


def test_text_shows_versions(rich_result):
    text = render_text(rich_result)
    assert "v1" in text
    assert "v2" in text


def test_text_shows_highest_risk(rich_result):
    text = render_text(rich_result)
    assert "CRITICAL" in text


def test_text_groups_by_risk(rich_result):
    text = render_text(rich_result)
    assert "[CRITICAL]" in text
    assert "[LOW]" in text


def test_markdown_empty_result(empty_result):
    md = render_markdown(empty_result)
    assert "_No changes detected._" in md


def test_markdown_has_heading(rich_result):
    md = render_markdown(rich_result)
    assert md.startswith("## Schema Classification")


def test_markdown_contains_risk_sections(rich_result):
    md = render_markdown(rich_result)
    assert "Critical" in md or "critical" in md.lower()


def test_json_is_valid(rich_result):
    out = render_json(rich_result)
    data = json.loads(out)
    assert data["from_version"] == "v1"
    assert "changes" in data


def test_render_dispatches_text(rich_result):
    assert render(rich_result, fmt="text") == render_text(rich_result)


def test_render_dispatches_markdown(rich_result):
    assert render(rich_result, fmt="markdown") == render_markdown(rich_result)


def test_render_dispatches_json(rich_result):
    assert render(rich_result, fmt="json") == render_json(rich_result)


def test_render_writes_to_out(rich_result):
    import io
    buf = io.StringIO()
    render(rich_result, fmt="text", out=buf)
    assert len(buf.getvalue()) > 0
