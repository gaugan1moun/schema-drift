"""Tests for schema_drift.snapshot_diff_summary."""
import pytest

from schema_drift.diff import ChangeType, DiffResult, SchemaChange
from schema_drift.snapshot_diff_summary import (
    SnapshotDiffSummary,
    build_summary,
    render_markdown,
    render_text,
)


def _change(table: str, column: str, change_type: ChangeType) -> SchemaChange:
    return SchemaChange(
        table=table,
        column=column,
        change_type=change_type,
        detail=f"{change_type.value} on {table}.{column}",
    )


@pytest.fixture()
def empty_diff() -> DiffResult:
    return DiffResult(from_version="v1", to_version="v2", changes=[])


@pytest.fixture()
def rich_diff() -> DiffResult:
    return DiffResult(
        from_version="v1",
        to_version="v2",
        changes=[
            _change("users", "email", ChangeType.COLUMN_ADDED),
            _change("users", "age", ChangeType.COLUMN_REMOVED),
            _change("orders", None, ChangeType.TABLE_ADDED),
        ],
    )


def test_build_summary_empty(empty_diff):
    summary = build_summary(empty_diff)
    assert summary.is_empty()
    assert summary.total_changes == 0
    assert summary.affected_tables == []
    assert summary.counts_by_type == {}


def test_build_summary_versions(rich_diff):
    summary = build_summary(rich_diff)
    assert summary.from_version == "v1"
    assert summary.to_version == "v2"


def test_build_summary_total_changes(rich_diff):
    summary = build_summary(rich_diff)
    assert summary.total_changes == 3


def test_build_summary_counts_by_type(rich_diff):
    summary = build_summary(rich_diff)
    assert summary.counts_by_type[ChangeType.COLUMN_ADDED.value] == 1
    assert summary.counts_by_type[ChangeType.COLUMN_REMOVED.value] == 1
    assert summary.counts_by_type[ChangeType.TABLE_ADDED.value] == 1


def test_build_summary_affected_tables_sorted(rich_diff):
    summary = build_summary(rich_diff)
    assert summary.affected_tables == ["orders", "users"]


def test_build_summary_no_zero_counts(rich_diff):
    summary = build_summary(rich_diff)
    for count in summary.counts_by_type.values():
        assert count > 0


def test_to_dict_structure(rich_diff):
    summary = build_summary(rich_diff)
    d = summary.to_dict()
    assert set(d.keys()) == {
        "from_version",
        "to_version",
        "total_changes",
        "counts_by_type",
        "affected_tables",
    }


def test_render_text_contains_versions(rich_diff):
    text = render_text(build_summary(rich_diff))
    assert "v1" in text
    assert "v2" in text


def test_render_text_contains_total(rich_diff):
    text = render_text(build_summary(rich_diff))
    assert "3" in text


def test_render_text_empty(empty_diff):
    text = render_text(build_summary(empty_diff))
    assert "0" in text


def test_render_markdown_contains_header(rich_diff):
    md = render_markdown(build_summary(rich_diff))
    assert md.startswith("## Diff Summary")


def test_render_markdown_lists_tables(rich_diff):
    md = render_markdown(build_summary(rich_diff))
    assert "`orders`" in md
    assert "`users`" in md
