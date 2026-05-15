"""Render a ChangeForecast in text, markdown, or JSON formats."""
from __future__ import annotations

import json

from schema_drift.change_forecast import ChangeForecast


def render_text(forecast: ChangeForecast) -> str:
    lines = ["Schema Change Forecast", "=" * 30]
    if forecast.is_empty():
        lines.append("No historical data available for forecasting.")
        return "\n".join(lines)

    lines.append(f"Window size : {forecast.window_size} periods")
    lines.append("")
    lines.append(f"{'Period':<18} {'Predicted':>10} {'Confidence':>12}")
    lines.append("-" * 42)
    for p in forecast.points:
        bar = int(p.confidence * 10)
        conf_str = f"{p.confidence:.0%} {'|' * bar}"
        lines.append(f"{p.period:<18} {p.predicted_changes:>10.1f} {conf_str:>12}")
    return "\n".join(lines)


def render_markdown(forecast: ChangeForecast) -> str:
    lines = ["## Schema Change Forecast", ""]
    if forecast.is_empty():
        lines.append("_No historical data available for forecasting._")
        return "\n".join(lines)

    lines.append(f"**Window size:** {forecast.window_size} periods")
    lines.append("")
    lines.append("| Period | Predicted Changes | Confidence |")
    lines.append("|--------|:-----------------:|:----------:|")
    for p in forecast.points:
        lines.append(f"| {p.period} | {p.predicted_changes:.1f} | {p.confidence:.0%} |")
    return "\n".join(lines)


def render_json(forecast: ChangeForecast) -> str:
    return json.dumps(forecast.to_dict(), indent=2)


def render(forecast: ChangeForecast, fmt: str = "text") -> str:
    if fmt == "markdown":
        return render_markdown(forecast)
    if fmt == "json":
        return render_json(forecast)
    return render_text(forecast)
