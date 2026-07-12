from __future__ import annotations

import csv
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any


def setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


class UploadRecorder:
    def __init__(self, log_dir: Path, fmt: str = "json") -> None:
        self.fmt = fmt
        self.log_dir = Path(log_dir)
        self.file: Path | None = None
        if fmt in ("json", "csv"):
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.file = self.log_dir / f"uploads.{fmt}"

    def record(self, filepath: str, result: dict[str, Any]) -> None:
        if self.fmt == "none" or self.file is None:
            return
        entry = {
            "file": filepath,
            "message_id": (result.get("result") or {}).get("message_id"),
            "ok": result.get("ok"),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
        if self.fmt == "json":
            with self.file.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        elif self.fmt == "csv":
            write_header = not self.file.exists()
            with self.file.open("a", encoding="utf-8", newline="") as fh:
                writer = csv.DictWriter(fh, fieldnames=list(entry.keys()))
                if write_header:
                    writer.writeheader()
                writer.writerow(entry)
