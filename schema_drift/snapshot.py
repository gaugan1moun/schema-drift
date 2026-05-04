"""Schema snapshot module for capturing and serializing database schema state."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, List, Optional


@dataclass
class ColumnSchema:
    name: str
    data_type: str
    nullable: bool = True
    default: Optional[str] = None
    primary_key: bool = False


@dataclass
class TableSchema:
    name: str
    columns: List[ColumnSchema] = field(default_factory=list)

    def get_column(self, name: str) -> Optional[ColumnSchema]:
        return next((c for c in self.columns if c.name == name), None)


@dataclass
class SchemaSnapshot:
    version: str
    captured_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    tables: Dict[str, TableSchema] = field(default_factory=dict)

    def add_table(self, table: TableSchema) -> None:
        self.tables[table.name] = table

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "captured_at": self.captured_at,
            "tables": {
                name: {
                    "name": t.name,
                    "columns": [asdict(c) for c in t.columns],
                }
                for name, t in self.tables.items()
            },
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict) -> SchemaSnapshot:
        snapshot = cls(
            version=data["version"],
            captured_at=data["captured_at"],
        )
        for table_name, table_data in data.get("tables", {}).items():
            table = TableSchema(
                name=table_name,
                columns=[
                    ColumnSchema(**col) for col in table_data.get("columns", [])
                ],
            )
            snapshot.tables[table_name] = table
        return snapshot

    @classmethod
    def from_json(cls, json_str: str) -> SchemaSnapshot:
        return cls.from_dict(json.loads(json_str))
