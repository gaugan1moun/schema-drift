"""Tests for schema_drift.alerting."""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from schema_drift.alerting import AlertConfig, alert, send_email_alert, send_slack_alert, _should_alert
from schema_drift.diff import DiffResult, SchemaChange, ChangeType
from schema_drift.snapshot import SchemaSnapshot


def _make_diff(has_changes: bool = True) -> DiffResult:
    changes = []
    if has_changes:
        changes.append(SchemaChange(change_type=ChangeType.COLUMN_ADDED, table="users", column="email"))
    snap_a = SchemaSnapshot(version="v1", tables={})
    snap_b = SchemaSnapshot(version="v2", tables={})
    return DiffResult(from_version="v1", to_version="v2", changes=changes)


@pytest.fixture
def cfg_email():
    return AlertConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="user@example.com",
        smtp_password="secret",
        email_from="drift@example.com",
        email_to=["admin@example.com"],
    )


@pytest.fixture
def cfg_slack():
    return AlertConfig(slack_webhook_url="https://hooks.slack.com/test")


def test_should_alert_with_changes():
    diff = _make_diff(has_changes=True)
    config = AlertConfig(only_on_changes=True)
    assert _should_alert(diff, config) is True


def test_should_not_alert_without_changes_when_only_on_changes():
    diff = _make_diff(has_changes=False)
    config = AlertConfig(only_on_changes=True)
    assert _should_alert(diff, config) is False


def test_should_alert_without_changes_when_flag_off():
    diff = _make_diff(has_changes=False)
    config = AlertConfig(only_on_changes=False)
    assert _should_alert(diff, config) is True


def test_send_email_raises_without_smtp_host():
    diff = _make_diff()
    config = AlertConfig(email_to=["a@b.com"])
    with pytest.raises(ValueError, match="smtp_host"):
        send_email_alert(diff, config)


def test_send_email_returns_false_when_no_changes(cfg_email):
    diff = _make_diff(has_changes=False)
    cfg_email.only_on_changes = True
    result = send_email_alert(diff, cfg_email)
    assert result is False


def test_send_email_calls_smtp(cfg_email):
    diff = _make_diff()
    with patch("schema_drift.alerting.smtplib.SMTP") as mock_smtp_cls:
        mock_server = MagicMock()
        mock_smtp_cls.return_value.__enter__ = lambda s: mock_server
        mock_smtp_cls.return_value.__exit__ = MagicMock(return_value=False)
        result = send_email_alert(diff, cfg_email)
    assert result is True


def test_send_slack_raises_without_url():
    diff = _make_diff()
    config = AlertConfig()
    with pytest.raises(ValueError, match="slack_webhook_url"):
        send_slack_alert(diff, config)


def test_send_slack_returns_false_when_no_changes(cfg_slack):
    diff = _make_diff(has_changes=False)
    cfg_slack.only_on_changes = True
    result = send_slack_alert(diff, cfg_slack)
    assert result is False


def test_alert_dispatches_both_channels(cfg_email):
    cfg_email.slack_webhook_url = "https://hooks.slack.com/test"
    diff = _make_diff()
    with patch("schema_drift.alerting.send_email_alert", return_value=True) as me, \
         patch("schema_drift.alerting.send_slack_alert", return_value=True) as ms:
        results = alert(diff, cfg_email)
    assert results == {"email": True, "slack": True}
    me.assert_called_once()
    ms.assert_called_once()
