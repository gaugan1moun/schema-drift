"""Tests for schema_drift.severity_summary."""
import pytest
from unittest.mock import MagicMock

from schema_drift.diff import ChangeType, SchemaChange, DiffResult
from schema_drift.audit import AuditEntry, AuditReport
from schema_drift.severity_summary import (
    severity_for,
    summarise_diff,
    summarise_audit,
    SeveritySummary,
)


def _change(ct: ChangeType) -> SchemaChange:
    return SchemaChange(change_type=ct, table="t", column=None, detail="")


def _diff(*change_types: ChangeType) -> DiffResult:
    changes = [_change(ct) for ct in change_types]
    return DiffResult(from_version="v1", to_version="v2", changes=changes)


# ---------------------------------------------------------------------------
# severity_for
# ---------------------------------------------------------------------------

def test_severity_for_table_removed():
    assert severity_for(ChangeType.TABLE_REMOVED) == "critical"


def test_severity_for_column_removed():
    assert severity_for(ChangeType.COLUMN_REMOVED) == "high"


def test_severity_for_table_added():
    assert severity_for(ChangeType.TABLE_ADDED) == "medium"


def test_severity_for_nullable_changed():
    assert severity_for(ChangeType.NULLABLE_CHANGED) == "low"


# ---------------------------------------------------------------------------
# summarise_diff
# ---------------------------------------------------------------------------

def test_summarise_diff_empty():
    result = summarise_diff(_diff())
    assert result.total() == 0
    assert result.is_empty()


def test_summarise_diff_counts_correctly():
    result = summarise_diff(_diff(
        ChangeType.TABLE_REMOVED,
        ChangeType.COLUMN_REMOVED,
        ChangeType.COLUMN_ADDED,
    ))
    assert result.counts["critical"] == 1
    assert result.counts["high"] == 1
    assert result.counts["medium"] == 1
    assert result.total() == 3


def test_summarise_diff_highest_critical():
    result = summarise_diff(_diff(ChangeType.TABLE_REMOVED, ChangeType.COLUMN_ADDED))
    assert result.highest == "critical"


def test_summarise_diff_highest_medium_when_no_critical_or_high():
    result = summarise_diff(_diff(ChangeType.COLUMN_ADDED, ChangeType.TABLE_ADDED))
    assert result.highest == "medium"


def test_summarise_diff_to_dict_keys():
    result = summarise_diff(_diff(ChangeType.TYPE_CHANGED))
    d = result.to_dict()
    assert "counts" in d
    assert "highest" in d
    assert "total" in d
    assert d["total"] == 1


# ---------------------------------------------------------------------------
# summarise_audit
# ---------------------------------------------------------------------------

def _make_entry(version_pair, *change_types):
    diff = _diff(*change_types)
    diff.from_version, diff.to_version = version_pair
    entry = AuditEntry(from_version=version_pair[0], to_version=version_pair[1], diff=diff)
    return entry


def test_summarise_audit_empty_report():
    report = AuditReport(entries=[])
    result = summarise_audit(report)
    assert result.is_empty()
    assert result.highest == "low"


def test_summarise_audit_aggregates_across_entries():
    e1 = _make_entry(("v1", "v2"), ChangeType.TABLE_REMOVED)
    e2 = _make_entry(("v2", "v3"), ChangeType.COLUMN_ADDED, ChangeType.DEFAULT_CHANGED)
    report = AuditReport(entries=[e1, e2])
    result = summarise_audit(report)
    assert result.counts["critical"] == 1
    assert result.counts["medium"] == 1
    assert result.counts["low"] == 1
    assert result.total() == 3
    assert result.highest == "critical"
