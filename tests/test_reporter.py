"""Tests for schema_drift.reporter."""

import json
import pytest

from schema_drift.diff import DiffResult, SchemaChange, ChangeType
from schema_drift.reporter import render, render_text, render_markdown, render_json


@pytest.fixture()
def empty_diff() -> DiffResult:
    return DiffResult(base_version="1", updated_version="2", changes=[])


@pytest.fixture()
def diff_with_changes() -> DiffResult:
    return DiffResult(
        base_version="1",
        updated_version="2",
        changes=[
            SchemaChange(
                change_type=ChangeType.ADDED,
                table="users",
                column="email",
                description="Column added",
            ),
            SchemaChange(
                change_type=ChangeType.REMOVED,
                table="orders",
                column="legacy_id",
                description="Column removed",
            ),
            SchemaChange(
                change_type=ChangeType.MODIFIED,
                table="products",
                column="price",
                description="Type changed from INTEGER to NUMERIC",
            ),
        ],
    )


# --- text ---

def test_text_no_changes(empty_diff):
    output = render_text(empty_diff)
    assert "No schema changes detected." in output
    assert "v1 → v2" in output


def test_text_lists_changes(diff_with_changes):
    output = render_text(diff_with_changes)
    assert "[+] users.email" in output
    assert "[-] orders.legacy_id" in output
    assert "[~] products.price" in output
    assert "Total changes: 3" in output


# --- markdown ---

def test_markdown_no_changes(empty_diff):
    output = render_markdown(empty_diff)
    assert "_No schema changes detected._" in output


def test_markdown_has_table_rows(diff_with_changes):
    output = render_markdown(diff_with_changes)
    assert "`users`" in output
    assert "`+`" in output
    assert "**Total changes:** 3" in output


# --- json ---

def test_json_structure(diff_with_changes):
    output = render_json(diff_with_changes)
    data = json.loads(output)
    assert data["base_version"] == "1"
    assert data["updated_version"] == "2"
    assert data["has_changes"] is True
    assert len(data["changes"]) == 3
    assert data["changes"][0]["change_type"] == "added"


def test_json_no_changes(empty_diff):
    data = json.loads(render_json(empty_diff))
    assert data["has_changes"] is False
    assert data["changes"] == []


# --- render dispatch ---

def test_render_defaults_to_text(diff_with_changes):
    assert render(diff_with_changes) == render_text(diff_with_changes)


def test_render_json_format(diff_with_changes):
    assert render(diff_with_changes, fmt="json") == render_json(diff_with_changes)


def test_render_markdown_format(diff_with_changes):
    assert render(diff_with_changes, fmt="markdown") == render_markdown(diff_with_changes)
