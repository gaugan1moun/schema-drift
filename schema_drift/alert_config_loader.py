"""Load AlertConfig from a JSON or dict source."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Union

from schema_drift.alerting import AlertConfig


def config_from_dict(data: dict) -> AlertConfig:
    """Build an AlertConfig from a plain dictionary."""
    return AlertConfig(
        smtp_host=data.get("smtp_host"),
        smtp_port=int(data.get("smtp_port", 587)),
        smtp_user=data.get("smtp_user"),
        smtp_password=data.get("smtp_password"),
        email_from=data.get("email_from"),
        email_to=list(data.get("email_to") or []),
        slack_webhook_url=data.get("slack_webhook_url"),
        only_on_changes=bool(data.get("only_on_changes", True)),
    )


def config_to_dict(config: AlertConfig) -> dict:
    """Serialise an AlertConfig to a plain dictionary."""
    return {
        "smtp_host": config.smtp_host,
        "smtp_port": config.smtp_port,
        "smtp_user": config.smtp_user,
        "smtp_password": config.smtp_password,
        "email_from": config.email_from,
        "email_to": config.email_to,
        "slack_webhook_url": config.slack_webhook_url,
        "only_on_changes": config.only_on_changes,
    }


def load_config(path: Union[str, Path]) -> AlertConfig:
    """Load an AlertConfig from a JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Alert config file not found: {path}")
    with path.open() as fh:
        data = json.load(fh)
    return config_from_dict(data)


def save_config(config: AlertConfig, path: Union[str, Path]) -> None:
    """Persist an AlertConfig to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as fh:
        json.dump(config_to_dict(config), fh, indent=2)
