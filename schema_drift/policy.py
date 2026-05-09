"""Policy engine for enforcing schema change rules."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from schema_drift.diff import ChangeType, DiffResult, SchemaChange


@dataclass
class PolicyRule:
    """A single rule that can block or warn on specific change types."""

    name: str
    blocked_change_types: List[ChangeType] = field(default_factory=list)
    blocked_tables: List[str] = field(default_factory=list)
    warn_change_types: List[ChangeType] = field(default_factory=list)
    description: str = ""

    def check(self, change: SchemaChange) -> Optional[str]:
        """Return 'block', 'warn', or None for a given change."""
        if change.change_type in self.blocked_change_types:
            return "block"
        if change.table in self.blocked_tables and change.change_type in (
            ChangeType.COLUMN_REMOVED,
            ChangeType.TABLE_REMOVED,
        ):
            return "block"
        if change.change_type in self.warn_change_types:
            return "warn"
        return None


@dataclass
class PolicyViolation:
    """Represents a policy violation for a specific change."""

    rule_name: str
    level: str  # 'block' or 'warn'
    change: SchemaChange

    def __str__(self) -> str:
        return (
            f"[{self.level.upper()}] Rule '{self.rule_name}': "
            f"{self.change.change_type.value} on {self.change.table}"
            + (f".{self.change.column}" if self.change.column else "")
        )


@dataclass
class PolicyResult:
    """Result of evaluating all rules against a diff."""

    violations: List[PolicyViolation] = field(default_factory=list)

    @property
    def is_blocked(self) -> bool:
        return any(v.level == "block" for v in self.violations)

    @property
    def warnings(self) -> List[PolicyViolation]:
        return [v for v in self.violations if v.level == "warn"]

    @property
    def blocks(self) -> List[PolicyViolation]:
        return [v for v in self.violations if v.level == "block"]


def evaluate_policy(rules: List[PolicyRule], diff: DiffResult) -> PolicyResult:
    """Evaluate all rules against every change in the diff."""
    violations: List[PolicyViolation] = []
    for change in diff.changes:
        for rule in rules:
            level = rule.check(change)
            if level:
                violations.append(PolicyViolation(rule_name=rule.name, level=level, change=change))
    return PolicyResult(violations=violations)
