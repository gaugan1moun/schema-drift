"""Tests for schema_drift.change_classifier."""
import pytest
from schema_drift.diff import ChangeType, SchemaChange, DiffResult
from schema_drift.change_classifier import (
    risk_for_change,
    classify,
    ClassificationResult,
    ClassifiedChange,
)


def _change(ct: ChangeType, table: str = "users", column: str | None = None) -> SchemaChange:
    return SchemaChange(change_type=ct, table=table, column=column, detail="")


def _diff(*changes: SchemaChange) -> DiffResult:
    return DiffResult(from_version="v1", to_version="v2", changes=list(changes))


def test_risk_for_table_removed():
    assert risk_for_change(_change(ChangeType.TABLE_REMOVED)) == "critical"


def test_risk_for_column_removed():
    assert risk_for_change(_change(ChangeType.COLUMN_REMOVED, column="id")) == "high"


def test_risk_for_table_added():
    assert risk_for_change(_change(ChangeType.TABLE_ADDED)) == "low"


def test_risk_for_column_nullable_changed():
    assert risk_for_change(_change(ChangeType.COLUMN_NULLABLE_CHANGED, column="x")) == "medium"


def test_classify_empty_diff():
    result = classify(_diff())
    assert isinstance(result, ClassificationResult)
    assert result.classified == []
    assert result.highest_risk == "none"


def test_classify_populates_changes():
    diff = _diff(
        _change(ChangeType.COLUMN_ADDED, column="email"),
        _change(ChangeType.TABLE_REMOVED, table="legacy"),
    )
    result = classify(diff)
    assert len(result.classified) == 2


def test_classify_highest_risk_critical():
    diff = _diff(
        _change(ChangeType.COLUMN_ADDED, column="email"),
        _change(ChangeType.TABLE_REMOVED, table="legacy"),
    )
    result = classify(diff)
    assert result.highest_risk == "critical"


def test_classify_highest_risk_high_no_critical():
    diff = _diff(_change(ChangeType.COLUMN_REMOVED, column="age"))
    result = classify(diff)
    assert result.highest_risk == "high"


def test_by_risk_filters_correctly():
    diff = _diff(
        _change(ChangeType.COLUMN_ADDED, column="x"),
        _change(ChangeType.TABLE_REMOVED, table="old"),
    )
    result = classify(diff)
    assert len(result.by_risk("low")) == 1
    assert len(result.by_risk("critical")) == 1
    assert len(result.by_risk("medium")) == 0


def test_to_dict_structure():
    diff = _diff(_change(ChangeType.COLUMN_TYPE_CHANGED, column="status"))
    result = classify(diff)
    d = result.to_dict()
    assert d["from_version"] == "v1"
    assert d["to_version"] == "v2"
    assert "highest_risk" in d
    assert isinstance(d["changes"], list)
    assert d["changes"][0]["risk"] == "high"
