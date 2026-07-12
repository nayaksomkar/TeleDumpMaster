"""Tests for the upload recorder (JSON / CSV audit logs)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from teledumpmaster.logging_utils import UploadRecorder


def test_json_recorder(tmp_path: Path) -> None:
    rec = UploadRecorder(tmp_path, "json")
    rec.record("/a/file.mkv", {"ok": True, "result": {"message_id": 42}})
    rec.record("/a/file2.mkv", {"ok": True, "result": {"message_id": 43}})
    data = json.loads((tmp_path / "uploads.json").read_text())
    assert len(data) == 2
    assert data[0]["message_id"] == 42


def test_csv_recorder_writes_header_once(tmp_path: Path) -> None:
    rec = UploadRecorder(tmp_path, "csv")
    rec.record("/a/file.mkv", {"ok": True, "result": {"message_id": 1}})
    rec.record("/a/file2.mkv", {"ok": True, "result": {"message_id": 2}})
    with (tmp_path / "uploads.csv").open() as fh:
        reader = list(csv.DictReader(fh))
    assert len(reader) == 2
    assert reader[0]["message_id"] == "1"


def test_none_recorder_no_file(tmp_path: Path) -> None:
    rec = UploadRecorder(tmp_path, "none")
    rec.record("/a/file.mkv", {"ok": True})
    assert rec.file is None
