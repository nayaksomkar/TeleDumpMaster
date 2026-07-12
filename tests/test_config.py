"""Tests for configuration validation and parsing."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from teledumpmaster.config import Config
from teledumpmaster.exceptions import ConfigurationError


def test_config_from_env_defaults(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TELEDUMP_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEDUMP_CHANNEL_ID", "-1001")
    monkeypatch.setenv("TELEDUMP_UPLOAD_FOLDER", str(tmp_path))
    cfg = Config.from_env()
    assert cfg.retries == 3
    assert cfg.poll_interval == 5.0
    assert cfg.post_action == "keep"
    assert cfg.upload_folder == tmp_path


def test_config_missing_token_raises(monkeypatch) -> None:
    for key in list(__import__("os").environ):
        if key.startswith("TELEDUMP_"):
            monkeypatch.delenv(key, raising=False)
    with pytest.raises(ConfigurationError):
        Config.from_env()


def test_config_rejects_bad_post_action(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("TELEDUMP_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEDUMP_CHANNEL_ID", "-1001")
    monkeypatch.setenv("TELEDUMP_UPLOAD_FOLDER", str(tmp_path))
    monkeypatch.setenv("TELEDUMP_POST_ACTION", "explode")
    with pytest.raises(ConfigurationError):
        Config.from_env()


def test_config_loads_dotenv(tmp_path: Path, monkeypatch) -> None:
    for key in list(__import__("os").environ):
        if key.startswith("TELEDUMP_"):
            monkeypatch.delenv(key, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        textwrap.dedent(
            """
            TELEDUMP_BOT_TOKEN=tok
            TELEDUMP_CHANNEL_ID=-1001
            TELEDUMP_UPLOAD_FOLDER=./uploads
            TELEDUMP_POLL_INTERVAL=10
            """
        )
    )
    cfg = Config.from_env(dotenv_path=env_file)
    assert cfg.bot_token == "tok"
    assert cfg.poll_interval == 10.0
