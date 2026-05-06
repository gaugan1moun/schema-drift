"""Track a log of alerts that have been dispatched."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Union


@dataclass
class AlertRecord:
    """A single dispatched-alert record."""
    from_version: str
    to_version: str
    channels: list[str]
    change_count: int
    dispatched_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    success: bool = True


class AlertHistory:
    """Persist and query a log of past alerts."""

    def __init__(self, path: Union[str, Path]) -> None:
        self._path = Path(path)
        self._records: list[AlertRecord] = []
        if self._path.exists():
            self._load()

    def _load(self) -> None:
        with self._path.open() as fh:
            raw = json.load(fh)
        self._records = [AlertRecord(**r) for r in raw]

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("w") as fh:
            json.dump([asdict(r) for r in self._records], fh, indent=2)

    def record(self, entry: AlertRecord) -> None:
        """Append a new alert record and persist."""
        self._records.append(entry)
        self._save()

    def all(self) -> list[AlertRecord]:
        """Return all alert records."""
        return list(self._records)

    def successful(self) -> list[AlertRecord]:
        """Return only successful alert records."""
        return [r for r in self._records if r.success]

    def failed(self) -> list[AlertRecord]:
        """Return only failed alert records."""
        return [r for r in self._records if not r.success]

    def __len__(self) -> int:
        return len(self._records)
