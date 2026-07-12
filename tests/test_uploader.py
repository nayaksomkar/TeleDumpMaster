"""Tests for the Telegram uploader (network mocked)."""

from __future__ import annotations

from pathlib import Path

import pytest

from teledumpmaster.config import Config
from teledumpmaster.exceptions import UploadError
from teledumpmaster.uploader import TelegramUploader


def _cfg(tmp_path: Path) -> Config:
    return Config(
        bot_token="tok",
        channel_id="-1001",
        upload_folder=tmp_path,
    )


def test_send_document_success(tmp_path: Path, monkeypatch) -> None:
    payload = {"ok": True, "result": {"message_id": 99}}
    calls = {"n": 0}

    class FakeResp:
        status_code = 200

        def json(self):
            return payload

    class FakeSession:
        def post(self, *args, **kwargs):
            calls["n"] += 1
            return FakeResp()

    cfg = _cfg(tmp_path)
    monkeypatch.setattr("teledumpmaster.uploader.requests.Session", lambda: FakeSession())
    uploader = TelegramUploader(cfg)
    (tmp_path / "a.txt").write_text("hello")
    result = uploader.send_document(tmp_path / "a.txt")
    assert result == payload
    assert calls["n"] == 1


def test_send_document_retries_then_succeeds(tmp_path: Path, monkeypatch) -> None:
    calls = {"n": 0}

    class FakeResp:
        status_code = 200
        text = ""

        def json(self):
            if calls["n"] < 2:
                return {"ok": False, "description": "retry me"}
            return {"ok": True, "result": {"message_id": 1}}

    class FakeSession:
        def post(self, *args, **kwargs):
            calls["n"] += 1
            return FakeResp()

    monkeypatch.setattr("teledumpmaster.uploader.requests.Session", lambda: FakeSession())
    uploader = TelegramUploader(_cfg(tmp_path))
    (tmp_path / "a.txt").write_text("hello")
    result = uploader.send_document(tmp_path / "a.txt")
    assert result["ok"] is True
    assert calls["n"] == 2


def test_send_document_fails_after_retries(tmp_path: Path, monkeypatch) -> None:
    class FakeResp:
        status_code = 500
        text = "internal error"

        def json(self):
            return {"ok": False, "description": "boom"}

    class FakeSession:
        def post(self, *args, **kwargs):
            return FakeResp()

    monkeypatch.setattr("teledumpmaster.uploader.requests.Session", lambda: FakeSession())
    uploader = TelegramUploader(_cfg(tmp_path))
    (tmp_path / "a.txt").write_text("hello")
    with pytest.raises(UploadError):
        uploader.send_document(tmp_path / "a.txt")
