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


class Watcher:
    def __init__(self, config: Config, uploader: TelegramUploader | None = None) -> None:
        self.config = config
        self.uploader = uploader or TelegramUploader(config)
        self._uploaded: set[str] = set()

        if not config.upload_folder.is_dir():
            raise ConfigurationError(
                f"Upload folder does not exist: {config.upload_folder}"
            )

    def scan(self) -> list[str]:
        paths = [
            str(p) for p in self.config.upload_folder.iterdir() if p.is_file()
        ]
        return sort_paths(paths)

    def process_once(self, on_upload: Callable[[str, dict[str, Any]], None] | None = None) -> int:
        count = 0
        for filepath in self.scan():
            if filepath in self._uploaded:
                continue
            result = self.uploader.send_document(filepath)
            logger.info("Uploaded %s", Path(filepath).name)
            self._uploaded.add(filepath)
            self._post_action(Path(filepath))
            count += 1
            if on_upload:
                on_upload(filepath, result)
        return count

    def run_forever(self, on_upload: Callable[[str, dict[str, Any]], None] | None = None) -> None:
        logger.info("Watching %s every %ss", self.config.upload_folder, self.config.poll_interval)
        try:
            while True:
                self.process_once(on_upload=on_upload)
                time.sleep(self.config.poll_interval)
        except KeyboardInterrupt:
            logger.info("Stopped by user")

    def _post_action(self, filepath: Path) -> None:
        action = self.config.post_action
        if action == "delete":
            filepath.unlink(missing_ok=True)
            logger.debug("Deleted %s", filepath.name)
        elif action == "archive":
            self.config.archive_dir.mkdir(parents=True, exist_ok=True)
            target = self.config.archive_dir / filepath.name
            filepath.rename(target)
            logger.debug("Archived %s -> %s", filepath.name, target)
