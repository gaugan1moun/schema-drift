"""Schema diff module: compare two SchemaSnapshots and report changes."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List

from schema_drift.snapshot import SchemaSnapshot


class ChangeType(str, Enum):
    TABLE_ADDED = "table_added"
    TABLE_REMOVED = "table_removed"
    COLUMN_ADDED = "column_added"
    COLUMN_REMOVED = "column_removed"
    COLUMN_TYPE_CHANGED = "column_type_changed"
    COLUMN_NULLABLE_CHANGED = "column_nullable_changed"


@dataclass
class SchemaChange:
    change_type: ChangeType
    table: str
    column: str | None = None
    old_value: str | None = None
    new_value: str | None = None

    def __str__(self) -> str:
        if self.column:
            base = f"[{self.change_type}] {self.table}.{self.column}"
        else:
            base = f"[{self.change_type}] {self.table}"
        if self.old_value is not None or self.new_value is not None:
            base += f" ({self.old_value!r} -> {self.new_value!r})"
        return base


@dataclass
class DiffResult:
    old_version: str
    new_version: str
    changes: List[SchemaChange] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return len(self.changes) > 0

    def summary(self) -> str:
        if not self.has_changes:
            return f"No schema changes between {self.old_version} and {self.new_version}."
        lines = [f"Schema drift detected ({self.old_version} -> {self.new_version}):"]
        for change in self.changes:
            lines.append(f"  {change}")
        return "\n".join(lines)

    def changes_by_type(self, change_type: ChangeType) -> List[SchemaChange]:
        """Return all changes of a specific ChangeType."""
        return [c for c in self.changes if c.change_type == change_type]


def diff_snapshots(old: SchemaSnapshot, new: SchemaSnapshot) -> DiffResult:
    """Compare two snapshots and return a DiffResult with all detected changes."""
    result = DiffResult(old_version=old.version, new_version=new.version)

    old_tables = {t.name: t for t in old.tables}
    new_tables = {t.name: t for t in new.tables}

    for name in old_tables:
        if name not in new_tables:
            result.changes.append(SchemaChange(ChangeType.TABLE_REMOVED, table=name))

    for name in new_tables:
        if name not in old_tables:
            result.changes.append(SchemaChange(ChangeType.TABLE_ADDED, table=name))

    for name in old_tables:
        if name not in new_tables:
            continue
        old_cols = {c.name: c for c in old_tables[name].columns}
        new_cols = {c.name: c for c in new_tables[name].columns}

        for col_name in old_cols:
            if col_name not in new_cols:
                result.changes.append(
                    SchemaChange(ChangeType.COLUMN_REMOVED, table=name, column=col_name)
                )

        for col_name in new_cols:
            if col_name not in old_cols:
                result.changes.append(
                    SchemaChange(ChangeType.COLUMN_ADDED, table=name, column=col_name)
                )
            else:
                old_col = old_cols[col_name]
                new_col = new_cols[col_name]
                if old_col.data_type != new_col.data_type:
                    result.changes.append(
                        SchemaChange(
                            ChangeType.COLUMN_TYPE_CHANGED,
                            table=name,
                            column=col_name,
                            old_value=old_col.data_type,
                            new_value=new_col.data_type,
                        )
                    )
                if old_col.nullable != new_col.nullable:
                    result.changes.append(
                        SchemaChange(
                            ChangeType.COLUMN_NULLABLE_CHANGED,
                            table=name,
                            column=col_name,
                            old_value=str(old_col.nullable),
                            new_value=str(new_col.nullable),
                        )
                    )

    return result
