"""Track consecutive periods of schema change activity (streaks)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Optional

from schema_drift.rollup import RollupEntry


@dataclass
class StreakPoint:
    period: str
    total_changes: int

    def to_dict(self) -> dict:
        return {"period": self.period, "total_changes": self.total_changes}


@dataclass
class ChangeStreak:
    points: List[StreakPoint] = field(default_factory=list)
    current_streak: int = 0
    longest_streak: int = 0
    longest_streak_start: Optional[str] = None
    longest_streak_end: Optional[str] = None

    def is_empty(self) -> bool:
        return len(self.points) == 0

    def to_dict(self) -> dict:
        return {
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "longest_streak_start": self.longest_streak_start,
            "longest_streak_end": self.longest_streak_end,
            "points": [p.to_dict() for p in self.points],
        }


def _parse_period(period: str) -> date:
    """Parse a YYYY-MM-DD period label into a date."""
    return date.fromisoformat(period)


def build_streak(entries: List[RollupEntry], window_days: int = 1) -> ChangeStreak:
    """Compute change streaks from a list of RollupEntry objects.

    A streak is a run of consecutive periods (each separated by at most
    *window_days*) that all contain at least one schema change.
    """
    if not entries:
        return ChangeStreak()

    sorted_entries = sorted(entries, key=lambda e: e.period)
    points = [
        StreakPoint(period=e.period, total_changes=e.total_changes)
        for e in sorted_entries
    ]

    current_run: List[StreakPoint] = []
    best_run: List[StreakPoint] = []

    for point in points:
        if point.total_changes == 0:
            current_run = []
            continue

        if current_run:
            prev_date = _parse_period(current_run[-1].period)
            this_date = _parse_period(point.period)
            gap = (this_date - prev_date).days
            if gap <= window_days:
                current_run.append(point)
            else:
                current_run = [point]
        else:
            current_run = [point]

        if len(current_run) > len(best_run):
            best_run = list(current_run)

    streak = ChangeStreak(points=points)
    streak.current_streak = len(current_run)
    streak.longest_streak = len(best_run)
    if best_run:
        streak.longest_streak_start = best_run[0].period
        streak.longest_streak_end = best_run[-1].period
    return streak
