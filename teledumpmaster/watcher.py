# Folder watcher — scans, sorts, and uploads new files.
# Reports progress via callbacks so the CLI can display beautiful progress bars.

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .config import Config
from .exceptions import ConfigurationError
from .sorter import sort_paths
from .uploader import TelegramUploader

logger = logging.getLogger("teledumpmaster.watcher")


def _format_size(n: float) -> str:
    """Convert bytes to human-readable (KB, MB, GB)."""
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TB"


def _format_speed(bytes_: float, sec: float) -> str:
    """Convert bytes-per-sec to human-readable transfer rate."""
    if sec <= 0:
        return "—"
    return _format_size(bytes_ / sec) + "/s"


class Watcher:
    """Watch upload_folder and upload new files in natural order.

    Keeps a set of already-uploaded filenames so files are not re-uploaded
    between scan cycles (for the lifetime of the Watcher instance).
    """

    def __init__(self, config: Config, uploader: TelegramUploader | None = None) -> None:
        self.config = config
        self.uploader = uploader or TelegramUploader(config)
        self._uploaded: set[str] = set()

        if not config.upload_folder.is_dir():
            raise ConfigurationError(f"Upload folder does not exist: {config.upload_folder}")

    def scan(self) -> list[str]:
        """List all files in the upload directory, sorted in natural order."""
        paths = [str(p) for p in self.config.upload_folder.iterdir() if p.is_file()]
        return sort_paths(paths)

    def process_once(
        self,
        on_upload: Callable[[str, dict[str, Any]], None] | None = None,
        on_progress: Callable[[dict[str, Any]], None] | None = None,
        on_bytes: Callable[[int], None] | None = None,
    ) -> dict[str, Any]:
        """Upload all pending files once.

        For each file, calls on_progress(state_dict) where state_dict has:
          - status: "uploading" or "done"
          - current, total, file, size, speed, elapsed, action

        If on_bytes is provided, it is forwarded to the uploader for per-byte
        progress tracking.

        Returns summary: {files, total_size, total_time, avg_speed}
        """
        files = [f for f in self.scan() if f not in self._uploaded]
        if not files:
            return {"files": 0, "total_size": 0, "total_time": 0, "avg_speed": 0}

        total_size = 0
        total_time = 0.0

        for i, filepath in enumerate(files):
            fpath = Path(filepath)
            fsize_before = fpath.stat().st_size

            if on_progress:
                on_progress({
                    "status": "uploading",
                    "current": i + 1,
                    "total": len(files),
                    "file": fpath.name,
                    "size": fsize_before,
                })

            result = self.uploader.send_document(filepath, on_bytes=on_bytes)
            meta = result.get("_meta", {})
            fsize = meta.get("file_size", fsize_before)
            elapsed = meta.get("elapsed_sec", 0)

            total_size += fsize
            total_time += elapsed

            self._uploaded.add(filepath)
            action_result = self._post_action(fpath)

            if on_progress:
                on_progress({
                    "status": "done",
                    "current": i + 1,
                    "total": len(files),
                    "file": fpath.name,
                    "size": fsize,
                    "speed": fsize / elapsed if elapsed > 0 else 0,
                    "elapsed": elapsed,
                    "action": action_result,
                })

            if on_upload:
                on_upload(filepath, result)

        avg = total_size / total_time if total_time > 0 else 0
        return {
            "files": len(files),
            "total_size": total_size,
            "total_time": round(total_time, 2),
            "avg_speed": round(avg, 2),
        }

    def run_forever(
        self,
        on_upload: Callable[[str, dict[str, Any]], None] | None = None,
        on_bytes: Callable[[int], None] | None = None,
    ) -> None:
        """Watch the upload folder in an infinite loop, sleeping between scans.

        Press Ctrl+C to stop gracefully.
        """
        logger.info("Watching %s every %ss", self.config.upload_folder, self.config.poll_interval)
        try:
            while True:
                summary = self.process_once(on_upload=on_upload, on_bytes=on_bytes)
                if summary["files"]:
                    logger.info(
                        "Cycle done: %d file(s), %s, avg %s",
                        summary["files"],
                        _format_size(summary["total_size"]),
                        _format_speed(summary["total_size"], summary["total_time"]),
                    )
                time.sleep(self.config.poll_interval)
        except KeyboardInterrupt:
            logger.info("Stopped by user")

    def _post_action(self, filepath: Path) -> str | None:
        """Apply the configured action after a successful upload.
        Returns a short label describing what happened (or None for keep).
        """
        action = self.config.post_action
        if action == "delete":
            filepath.unlink(missing_ok=True)
            logger.info("Deleted %s", filepath.name)
            return "deleted"
        if action == "archive":
            self.config.archive_dir.mkdir(parents=True, exist_ok=True)
            target = self.config.archive_dir / filepath.name
            filepath.rename(target)
            logger.info("Archived %s", filepath.name)
            return "archived"
        return None
