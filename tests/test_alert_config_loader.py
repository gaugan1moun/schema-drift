"""Tests for schema_drift.alert_config_loader."""
from __future__ import annotations

import json
import pytest
from pathlib import Path

from schema_drift.alerting import AlertConfig
from schema_drift.alert_config_loader import (
    config_from_dict,
    config_to_dict,
    load_config,
    save_config,
)


SAMPLE_DICT = {
    "smtp_host": "smtp.example.com",
    "smtp_port": 465,
    "smtp_user": "user",
    "smtp_password": "pw",
    "email_from": "from@example.com",
    "email_to": ["a@example.com", "b@example.com"],
    "slack_webhook_url": "https://hooks.slack.com/xyz",
    "only_on_changes": True,
}


def test_config_from_dict_fields():
    cfg = config_from_dict(SAMPLE_DICT)
    assert cfg.smtp_host == "smtp.example.com"
    assert cfg.smtp_port == 465
    assert cfg.email_to == ["a@example.com", "b@example.com"]
    assert cfg.slack_webhook_url == "https://hooks.slack.com/xyz"
    assert cfg.only_on_changes is True


def test_config_from_dict_defaults():
    cfg = config_from_dict({})
    assert cfg.smtp_host is None
    assert cfg.smtp_port == 587
    assert cfg.email_to == []
    assert cfg.only_on_changes is True


def test_config_to_dict_roundtrip():
    cfg = config_from_dict(SAMPLE_DICT)
    result = config_to_dict(cfg)
    assert result["smtp_host"] == SAMPLE_DICT["smtp_host"]
    assert result["email_to"] == SAMPLE_DICT["email_to"]
    assert result["smtp_port"] == SAMPLE_DICT["smtp_port"]


def test_save_and_load_config(tmp_path):
    cfg = config_from_dict(SAMPLE_DICT)
    path = tmp_path / "alert.json"
    save_config(cfg, path)
    assert path.exists()
    loaded = load_config(path)
    assert loaded.smtp_host == cfg.smtp_host
    assert loaded.email_to == cfg.email_to
    assert loaded.slack_webhook_url == cfg.slack_webhook_url


def test_save_creates_parent_dirs(tmp_path):
    cfg = AlertConfig(smtp_host="localhost")
    path = tmp_path / "nested" / "dir" / "alert.json"
    save_config(cfg, path)
    assert path.exists()


def test_load_config_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nonexistent.json")


def test_save_writes_valid_json(tmp_path):
    cfg = config_from_dict(SAMPLE_DICT)
    path = tmp_path / "alert.json"
    save_config(cfg, path)
    with path.open() as fh:
        data = json.load(fh)
    assert data["smtp_host"] == "smtp.example.com"
