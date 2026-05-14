"""Serialization and deserialization of SchemaSnapshot to/from JSON."""

import json
from datetime import datetime
from typing import Union

from schema_drift.snapshot import ColumnSchema, TableSchema, SchemaSnapshot


def snapshot_to_dict(snapshot: SchemaSnapshot) -> dict:
    """Convert a SchemaSnapshot to a plain dictionary."""
    return {
        "version": snapshot.version,
        "captured_at": snapshot.captured_at.isoformat(),
        "tables": {
            name: {
                "name": table.name,
                "columns": {
                    col_name: {
                        "name": col.name,
                        "data_type": col.data_type,
                        "nullable": col.nullable,
                        "default": col.default,
                    }
                    for col_name, col in table.columns.items()
                },
            }
            for name, table in snapshot.tables.items()
        },
    }


def snapshot_from_dict(data: dict) -> SchemaSnapshot:
    """Reconstruct a SchemaSnapshot from a plain dictionary."""
    for required_key in ("version", "captured_at", "tables"):
        if required_key not in data:
            raise ValueError(f"Missing required key in snapshot data: '{required_key}'")

    tables = {}
    for table_name, table_data in data.get("tables", {}).items():
        if "name" not in table_data:
            raise ValueError(f"Missing 'name' for table '{table_name}'")
        columns = {}
        for col_name, col_data in table_data.get("columns", {}).items():
            for required_col_key in ("name", "data_type"):
                if required_col_key not in col_data:
                    raise ValueError(
                        f"Missing '{required_col_key}' for column '{col_name}' "
                        f"in table '{table_name}'"
                    )
            columns[col_name] = ColumnSchema(
                name=col_data["name"],
                data_type=col_data["data_type"],
                nullable=col_data.get("nullable", True),
                default=col_data.get("default"),
            )
        tables[table_name] = TableSchema(name=table_data["name"], columns=columns)

    try:
        captured_at = datetime.fromisoformat(data["captured_at"])
    except (ValueError, TypeError) as exc:
        raise ValueError(f"Invalid 'captured_at' timestamp: {data['captured_at']!r}") from exc

    return SchemaSnapshot(
        version=data["version"],
        captured_at=captured_at,
        tables=tables,
    )


def dump(snapshot: SchemaSnapshot, fp, indent: int = 2) -> None:
    """Serialize a SchemaSnapshot to a JSON file object."""
    json.dump(snapshot_to_dict(snapshot), fp, indent=indent)


def dumps(snapshot: SchemaSnapshot, indent: int = 2) -> str:
    """Serialize a SchemaSnapshot to a JSON string."""
    return json.dumps(snapshot_to_dict(snapshot), indent=indent)


def load(fp) -> SchemaSnapshot:
    """Deserialize a SchemaSnapshot from a JSON file object."""
    data = json.load(fp)
    return snapshot_from_dict(data)


def loads(s: Union[str, bytes]) -> SchemaSnapshot:
    """Deserialize a SchemaSnapshot from a JSON string."""
    data = json.loads(s)
    return snapshot_from_dict(data)
