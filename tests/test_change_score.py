"""Tests for schema_drift.change_score."""
import pytest
from schema_drift.diff import DiffResult, SchemaChange, ChangeType
from schema_drift.change_score import (
    weight_for,
    score_diff,
    score_multiple,
    ScoredDiff,
)


def _change(ct: ChangeType) -> SchemaChange:
    return SchemaChange(change_type=ct, table="t", column=None, detail="")


def _diff(*types: ChangeType) -> DiffResult:
    return DiffResult(
        from_version="v1",
        to_version="v2",
        changes=[_change(ct) for ct in types],
    )


def test_weight_for_table_removed():
    assert weight_for(ChangeType.TABLE_REMOVED) == 10


def test_weight_for_column_added():
    assert weight_for(ChangeType.COLUMN_ADDED) == 1


def test_score_diff_empty():
    result = score_diff(_diff())
    assert result.score == 0
    assert result.risk_level == "low"


def test_score_diff_single_table_removed():
    result = score_diff(_diff(ChangeType.TABLE_REMOVED))
    assert result.score == 10
    assert result.risk_level == "medium"


def test_score_diff_accumulates():
    result = score_diff(_diff(ChangeType.TABLE_REMOVED, ChangeType.COLUMN_REMOVED))
    assert result.score == 18


def test_score_diff_breakdown_keys():
    result = score_diff(_diff(ChangeType.TABLE_REMOVED, ChangeType.COLUMN_ADDED))
    assert ChangeType.TABLE_REMOVED in result.breakdown
    assert ChangeType.COLUMN_ADDED in result.breakdown


def test_risk_level_critical():
    changes = [ChangeType.TABLE_REMOVED] * 7  # 70 pts
    result = score_diff(_diff(*changes))
    assert result.risk_level == "critical"


def test_risk_level_high():
    changes = [ChangeType.TABLE_REMOVED] * 4  # 40 pts
    result = score_diff(_diff(*changes))
    assert result.risk_level == "high"


def test_score_multiple_length():
    diffs = [_diff(ChangeType.COLUMN_ADDED), _diff(ChangeType.TABLE_REMOVED)]
    results = score_multiple(diffs)
    assert len(results) == 2


def test_score_multiple_empty():
    """score_multiple should return an empty list when given no diffs."""
    results = score_multiple([])
    assert results == []


def test_score_multiple_preserves_order():
    """score_multiple should return results in the same order as the input diffs."""
    diffs = [
        _diff(ChangeType.COLUMN_ADDED),   # score 1
        _diff(ChangeType.TABLE_REMOVED),  # score 10
        _diff(ChangeType.COLUMN_REMOVED), # score 8
    ]
    results = score_multiple(diffs)
    assert [r.score for r in results] == [1, 10, 8]


def test_to_dict_contains_risk_level():
    result = score_diff(_diff(ChangeType.COLUMN_REMOVED))
    d = result.to_dict()
    assert "risk_level" in d
    assert d["score"] == 8


def test_scored_diff_versions():
    result = score_diff(_diff())
    assert result.from_version == "v1"
    assert result.to_version == "v2"
