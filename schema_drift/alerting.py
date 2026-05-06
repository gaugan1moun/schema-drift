"""Alerting module: send notifications when schema drift is detected."""
from __future__ import annotations

import smtplib
import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from email.mime.text import MIMEText
from typing import Optional

from schema_drift.diff import DiffResult
from schema_drift.reporter import render_text


@dataclass
class AlertConfig:
    """Configuration for alert channels."""
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: list[str] = field(default_factory=list)
    slack_webhook_url: Optional[str] = None
    only_on_changes: bool = True


def _should_alert(diff: DiffResult, config: AlertConfig) -> bool:
    """Return True if an alert should be sent for this diff."""
    if config.only_on_changes and not diff.has_changes:
        return False
    return True


def send_email_alert(diff: DiffResult, config: AlertConfig) -> bool:
    """Send an email alert for the given diff. Returns True on success."""
    if not _should_alert(diff, config):
        return False
    if not config.smtp_host or not config.email_to:
        raise ValueError("smtp_host and email_to are required for email alerts")

    body = render_text(diff)
    subject = (
        f"Schema drift detected: {diff.from_version} -> {diff.to_version}"
        if diff.has_changes
        else f"No schema changes: {diff.from_version} -> {diff.to_version}"
    )
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = config.email_from or config.smtp_user or "schema-drift@localhost"
    msg["To"] = ", ".join(config.email_to)

    with smtplib.SMTP(config.smtp_host, config.smtp_port) as server:
        if config.smtp_user and config.smtp_password:
            server.starttls()
            server.login(config.smtp_user, config.smtp_password)
        server.sendmail(msg["From"], config.email_to, msg.as_string())
    return True


def send_slack_alert(diff: DiffResult, config: AlertConfig) -> bool:
    """Send a Slack webhook alert for the given diff. Returns True on success."""
    if not _should_alert(diff, config):
        return False
    if not config.slack_webhook_url:
        raise ValueError("slack_webhook_url is required for Slack alerts")

    summary = render_text(diff)
    payload = json.dumps({"text": f"```{summary}```"}).encode()
    req = urllib.request.Request(
        config.slack_webhook_url,
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.status == 200


def alert(diff: DiffResult, config: AlertConfig) -> dict[str, bool]:
    """Dispatch alerts to all configured channels. Returns per-channel results."""
    results: dict[str, bool] = {}
    if config.smtp_host and config.email_to:
        results["email"] = send_email_alert(diff, config)
    if config.slack_webhook_url:
        results["slack"] = send_slack_alert(diff, config)
    return results
