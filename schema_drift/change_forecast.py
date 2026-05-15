"""Forecast future schema change activity based on historical rollup data."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from schema_drift.rollup import RollupEntry


@dataclass
class ForecastPoint:
    period: str
    predicted_changes: float
    confidence: float  # 0.0 – 1.0

    def to_dict(self) -> dict:
        return {
            "period": self.period,
            "predicted_changes": round(self.predicted_changes, 2),
            "confidence": round(self.confidence, 2),
        }


@dataclass
class ChangeForecast:
    window_size: int
    points: List[ForecastPoint] = field(default_factory=list)

    def is_empty(self) -> bool:
        return len(self.points) == 0

    def next_predicted(self) -> Optional[ForecastPoint]:
        return self.points[0] if self.points else None

    def to_dict(self) -> dict:
        return {
            "window_size": self.window_size,
            "points": [p.to_dict() for p in self.points],
        }


def _moving_average(values: List[float], window: int) -> List[float]:
    averages: List[float] = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        averages.append(sum(values[start : i + 1]) / (i - start + 1))
    return averages


def build_forecast(
    entries: List[RollupEntry],
    horizon: int = 3,
    window_size: int = 4,
) -> ChangeForecast:
    """Produce a simple moving-average forecast for the next *horizon* periods."""
    if not entries:
        return ChangeForecast(window_size=window_size)

    totals = [e.total_changes for e in entries]
    averages = _moving_average(totals, window_size)
    last_avg = averages[-1]

    # Confidence degrades with each step into the future.
    points: List[ForecastPoint] = []
    for step in range(1, horizon + 1):
        label = f"forecast+{step}"
        confidence = max(0.0, 1.0 - (step - 1) * 0.2)
        points.append(ForecastPoint(period=label, predicted_changes=last_avg, confidence=confidence))

    return ChangeForecast(window_size=window_size, points=points)
