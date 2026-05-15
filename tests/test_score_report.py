"""Tests for schema_drift.score_report."""
import json
import pytest
from schema_drift.diff import ChangeType
from schema_drift.change_score import score_diff, ScoredDiff
from schema_drift.diff import DiffResult, SchemaChange
from schema_drift.score_report import render_text, render_markdown, render_json, render


def _diff(*types: ChangeType) -> DiffResult:
    return DiffResult(
        from_version="v1",
        to_version="v2",
        changes=[
            SchemaChange(change_type=ct, table="orders", column=None, detail="")
            for ct in types
        ],
    )


@pytest.fixture
def low_score() -> ScoredDiff:
    return score_diff(_diff())


@pytest.fixture
def high_score() -> ScoredDiff:
    return score_diff(_diff(ChangeType.TABLE_REMOVED, ChangeType.COLUMN_REMOVED))


def test_render_text_contains_versions(high_score):
    out = render_text(high_score)
    assert "v1" in out and "v2" in out


def test_render_text_contains_score(high_score):
    out = render_text(high_score)
    assert str(high_score.score) in out


def test_render_text_contains_risk_level(high_score):
    out = render_text(high_score)
    assert high_score.risk_level.upper() in out


def test_render_text_breakdown_present(high_score):
    out = render_text(high_score)
    assert "Breakdown" in out


def test_render_markdown_heading(high_score):
    out = render_markdown(high_score)
    assert out.startswith("## Score Report")


def test_render_markdown_table_row(high_score):
    out = render_markdown(high_score)
    assert "|" in out


def test_render_json_valid(high_score):
    out = render_json(high_score)
    data = json.loads(out)
    assert data["score"] == high_score.score
    assert data["risk_level"] == high_score.risk_level


def test_render_json_breakdown_serialised(high_score):
    data = json.loads(render_json(high_score))
    assert isinstance(data["breakdown"], dict)


def test_render_dispatches_text(high_score):
    assert render(high_score, "text") == render_text(high_score)


def test_render_dispatches_markdown(high_score):
    assert render(high_score, "markdown") == render_markdown(high_score)


def test_render_dispatches_json(high_score):
    assert render(high_score, "json") == render_json(high_score)


def test_render_default_is_text(low_score):
    assert render(low_score) == render_text(low_score)
