"""Load and save PolicyRule definitions from YAML/JSON config files."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from schema_drift.diff import ChangeType
from schema_drift.policy import PolicyRule


def _change_type_from_str(value: str) -> ChangeType:
    for member in ChangeType:
        if member.value == value:
            return member
    raise ValueError(f"Unknown ChangeType: {value!r}")


def rule_from_dict(data: Dict[str, Any]) -> PolicyRule:
    """Deserialise a single rule from a plain dict."""
    return PolicyRule(
        name=data["name"],
        description=data.get("description", ""),
        blocked_change_types=[
            _change_type_from_str(v) for v in data.get("blocked_change_types", [])
        ],
        blocked_tables=data.get("blocked_tables", []),
        warn_change_types=[
            _change_type_from_str(v) for v in data.get("warn_change_types", [])
        ],
    )


def rule_to_dict(rule: PolicyRule) -> Dict[str, Any]:
    """Serialise a PolicyRule to a plain dict."""
    return {
        "name": rule.name,
        "description": rule.description,
        "blocked_change_types": [ct.value for ct in rule.blocked_change_types],
        "blocked_tables": rule.blocked_tables,
        "warn_change_types": [ct.value for ct in rule.warn_change_types],
    }


def load_rules(path: Path) -> List[PolicyRule]:
    """Load a list of PolicyRule objects from a JSON file."""
    with open(path, "r", encoding="utf-8") as fh:
        raw: List[Dict[str, Any]] = json.load(fh)
    return [rule_from_dict(entry) for entry in raw]


def save_rules(rules: List[PolicyRule], path: Path) -> None:
    """Persist a list of PolicyRule objects to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump([rule_to_dict(r) for r in rules], fh, indent=2)
