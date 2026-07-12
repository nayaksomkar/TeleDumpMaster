"""Tests for the Watcher using a fake uploader."""

from __future__ import annotations

from pathlib import Path

from teledumpmaster.config import Config
from teledumpmaster.watcher import Watcher


class FakeUploader:
    def __init__(self) -> None:
        self.uploaded: list[str] = []

    def send_document(self, filepath, caption=None):
        self.uploaded.append(str(filepath))
        return {"ok": True, "result": {"message_id": len(self.uploaded)}}


def test_watcher_process_once_sorted(tmp_path: Path) -> None:
    for name in ["episode10.mkv", "episode1.mkv", "episode2.mkv"]:
        (tmp_path / name).write_text("x")
    cfg = Config(
        bot_token="tok",
        channel_id="-1001",
        upload_folder=tmp_path,
        post_action="keep",
    )
    fake = FakeUploader()
    watcher = Watcher(cfg, uploader=fake)
    count = watcher.process_once()
    assert count == 3
    assert [Path(p).name for p in fake.uploaded] == [
        "episode1.mkv",
        "episode2.mkv",
        "episode10.mkv",
    ]


def test_watcher_delete_action(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x")
    cfg = Config(
        bot_token="tok",
        channel_id="-1001",
        upload_folder=tmp_path,
        post_action="delete",
    )
    watcher = Watcher(cfg, uploader=FakeUploader())
    watcher.process_once()
    assert not (tmp_path / "a.txt").exists()


def test_watcher_archive_action(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("x")
    cfg = Config(
        bot_token="tok",
        channel_id="-1001",
        upload_folder=tmp_path,
        post_action="archive",
        archive_dir=tmp_path / "archive",
    )
    watcher = Watcher(cfg, uploader=FakeUploader())
    watcher.process_once()
    assert (tmp_path / "archive" / "a.txt").exists()
    assert not (tmp_path / "a.txt").exists()
