"""Periodic snapshot diffing scheduler using a simple polling loop."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from schema_drift.watcher import SnapshotWatcher
from schema_drift.diff import DiffResult, compute_diff
from schema_drift.audit import AuditEntry, AuditReport

logger = logging.getLogger(__name__)


@dataclass
class SchedulerConfig:
    """Configuration for the snapshot scheduler."""

    interval_seconds: float = 60.0
    max_iterations: Optional[int] = None  # None means run forever
    on_change: Optional[Callable[[DiffResult], None]] = None


@dataclass
class Scheduler:
    """Polls a snapshot file at a fixed interval and reports diffs."""

    watcher: SnapshotWatcher
    config: SchedulerConfig = field(default_factory=SchedulerConfig)
    _report: AuditReport = field(default_factory=AuditReport, init=False)
    _iteration: int = field(default=0, init=False)

    @property
    def report(self) -> AuditReport:
        return self._report

    def _handle_diff(self, diff: DiffResult) -> None:
        entry = AuditEntry(
            from_version=diff.from_version,
            to_version=diff.to_version,
            diff=diff,
        )
        self._report.entries.append(entry)

        if diff.has_changes():
            logger.info(
                "Schema change detected: %s -> %s (%d changes)",
                diff.from_version,
                diff.to_version,
                len(diff.changes),
            )
            if self.config.on_change:
                try:
                    self.config.on_change(diff)
                except Exception:  # pragma: no cover
                    logger.exception("on_change callback raised an exception")

    def run_once(self) -> Optional[DiffResult]:
        """Perform a single check cycle. Returns a DiffResult if a diff occurred."""
        result = self.watcher.check_once()
        if result is not None:
            self._handle_diff(result)
            self._iteration += 1
            return result
        self._iteration += 1
        return None

    def run(self, _sleep: Callable[[float], None] = time.sleep) -> None:
        """Block and poll indefinitely (or up to max_iterations)."""
        logger.info(
            "Scheduler starting — interval=%.1fs max_iterations=%s",
            self.config.interval_seconds,
            self.config.max_iterations,
        )
        iteration = 0
        while True:
            self.run_once()
            iteration += 1
            if (
                self.config.max_iterations is not None
                and iteration >= self.config.max_iterations
            ):
                break
            _sleep(self.config.interval_seconds)
