# Console logging setup and JSON/CSV audit trail for uploads.
# UploadRecorder creates an append-only log file (uploads.json or uploads.csv).

from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any


def setup_logging(level: int = logging.INFO) -> None:
    """Configure the root logger with a timestamped console output format."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class UploadRecorder:
    """Append-only audit log of every upload, written as JSON or CSV."""

    def __init__(self, log_dir: Path, fmt: str = "json") -> None:
        self.fmt = fmt
        self.log_dir = Path(log_dir)
        self.file: Path | None = None
        if fmt in ("json", "csv"):
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.file = self.log_dir / f"uploads.{fmt}"

    def record(self, filepath: str, result: dict[str, Any]) -> None:
        """Append one upload entry to the log file.

        The entry includes the file path, Telegram message ID, success flag,
        and the current timestamp.
        """
        if self.fmt == "none" or self.file is None:
            return
        entry = {
            "file": filepath,
            "message_id": (result.get("result") or {}).get("message_id"),
            "ok": result.get("ok"),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        if self.fmt == "json":
            # Read existing data, append new entry, write back as JSON array
            data: list[dict[str, Any]] = []
            if self.file.exists():
                try:
                    with self.file.open("r", encoding="utf-8") as fh:
                        data = json.load(fh)
                except json.JSONDecodeError:
                    data = []
            data.append(entry)
            with self.file.open("w", encoding="utf-8") as fh:
                json.dump(data, fh, indent=4, ensure_ascii=False)
        elif self.fmt == "csv":
            # Write header only on first write, then append rows
            write_header = not self.file.exists()
            with self.file.open("a", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(entry.keys()))
                if write_header:
                    writer.writeheader()
                writer.writerow(entry)
