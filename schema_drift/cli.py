"""Minimal CLI entry-point for schema-drift reporting.

Usage:
    python -m schema_drift.cli <base_snapshot.json> <updated_snapshot.json> [--format text|json|markdown]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from schema_drift.snapshot import SchemaSnapshot
from schema_drift.diff import compute_diff
from schema_drift.reporter import render, OutputFormat


def _load_snapshot(path: str) -> SchemaSnapshot:
    data = json.loads(Path(path).read_text())
    snapshot = SchemaSnapshot(version=data["version"])
    snapshot.captured_at = data.get("captured_at")
    for table_name, table_data in data.get("tables", {}).items():
        from schema_drift.snapshot import TableSchema, ColumnSchema
        columns = [
            ColumnSchema(name=c["name"], data_type=c["data_type"], nullable=c.get("nullable", True))
            for c in table_data.get("columns", [])
        ]
        snapshot.add_table(TableSchema(name=table_name, columns=columns))
    return snapshot


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schema-drift",
        description="Detect and report schema changes between two snapshots.",
    )
    parser.add_argument("base", help="Path to the base snapshot JSON file.")
    parser.add_argument("updated", help="Path to the updated snapshot JSON file.")
    parser.add_argument(
        "--format",
        dest="fmt",
        choices=["text", "json", "markdown"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when schema changes are detected.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        base = _load_snapshot(args.base)
        updated = _load_snapshot(args.updated)
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error loading snapshot: {exc}", file=sys.stderr)
        return 2

    result = compute_diff(base, updated)
    print(render(result, fmt=args.fmt))

    if args.exit_code and result.has_changes():
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
