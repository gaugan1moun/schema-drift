"""Detect anomalous spikes in schema change activity across rollup history."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from schema_drift.rollup import RollupEntry


@dataclass
class AnomalyPoint:
    period: str
    total_changes: int
    mean: float
    std_dev: float
    z_score: float

    def to_dict(self) -> dict:
        return {
            "period": self.period,
            "total_changes": self.total_changes,
            "mean": round(self.mean, 4),
            "std_dev": round(self.std_dev, 4),
            "z_score": round(self.z_score, 4),
        }


@dataclass
class AnomalyReport:
    points: List[AnomalyPoint] = field(default_factory=list)
    threshold: float = 2.0

    def is_empty(self) -> bool:
        return len(self.points) == 0

    def anomalies(self) -> List[AnomalyPoint]:
        return [p for p in self.points if abs(p.z_score) >= self.threshold]

    def worst(self) -> Optional[AnomalyPoint]:
        if not self.points:
            return None
        return max(self.points, key=lambda p: abs(p.z_score))

    def to_dict(self) -> dict:
        return {
            "threshold": self.threshold,
            "points": [p.to_dict() for p in self.points],
            "anomalies": [p.to_dict() for p in self.anomalies()],
        }


def _mean(values: List[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _std_dev(values: List[float], mean: float) -> float:
    if len(values) < 2:
        return 0.0
    variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1)
    return variance ** 0.5


def build_anomaly_report(
    entries: List[RollupEntry],
    threshold: float = 2.0,
) -> AnomalyReport:
    if not entries:
        return AnomalyReport(threshold=threshold)

    totals = [float(e.total_changes) for e in entries]
    mean = _mean(totals)
    std = _std_dev(totals, mean)

    points: List[AnomalyPoint] = []
    for entry, total in zip(entries, totals):
        z = (total - mean) / std if std > 0 else 0.0
        points.append(
            AnomalyPoint(
                period=entry.period,
                total_changes=entry.total_changes,
                mean=mean,
                std_dev=std,
                z_score=z,
            )
        )

    return AnomalyReport(points=points, threshold=threshold)
