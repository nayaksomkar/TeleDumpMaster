# Telegram Bot API uploader with retry, exponential backoff, and speed tracking.
# Uses the sendDocument method to upload files to a chat/channel.

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import requests

from .config import Config
from .exceptions import UploadError

_CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB — each chunk read takes ~4ms at SSD speed,
# giving the Rich render thread enough time to redraw between chunks


class TelegramUploader:
    """Upload files to a Telegram chat via the Bot API with retry logic.

    Each upload attempt measures elapsed time so callers can report speed.
    On success the Telegram API response is returned as-is.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()

    def send_document(
        self,
        filepath: str | Path,
        caption: str | None = None,
        on_bytes: Callable[[int], None] | None = None,
    ) -> dict[str, Any]:
        """Upload a single file to Telegram.

        When on_bytes is provided the file is read in 4 MB chunks so the
        progress callback fires at disk-I/O speed.  Each read() call releases
        the GIL inside CPython, letting the Rich display thread redraw the
        progress bar between chunks.

        Retries on transient failures using exponential backoff (1s, 2s, 4s…).
        Returns the Telegram API response dict, which includes file size info
        and the server's message_id on success.

        Raises UploadError if all attempts fail.
        """
        filepath = Path(filepath)
        api_url = f"{self.config.api_base}/bot{self.config.bot_token}/sendDocument"
        caption = caption if caption is not None else self.config.caption
        if caption == "__FILENAME__":
            caption = filepath.name
        last_error: Exception | None = None
        file_size = filepath.stat().st_size

        for attempt in range(1, self.config.retries + 1):
            start = time.monotonic()
            try:
                if on_bytes:
                    chunks: list[bytes] = []
                    with filepath.open("rb") as f:
                        while True:
                            chunk = f.read(_CHUNK_SIZE)
                            if not chunk:
                                break
                            chunks.append(chunk)
                            on_bytes(len(chunk))
                    file_data: bytes = b"".join(chunks)
                else:
                    file_data = filepath.read_bytes()
                response = self.session.post(api_url,
                    data={"chat_id": self.config.channel_id, "caption": caption or ""},
                    files={"document": (filepath.name, file_data)},
                    timeout=self.config.timeout,
                )
                elapsed = time.monotonic() - start
                payload: dict[str, Any] = response.json()

                if response.status_code == 200 and payload.get("ok"):
                    payload["_meta"] = {
                        "file_size": file_size,
                        "elapsed_sec": round(elapsed, 2),
                        "attempts": attempt,
                    }
                    return payload

                last_error = UploadError(
                    f"Telegram API error: {payload.get('description', response.text)}"
                )
            except requests.RequestException as exc:
                elapsed = time.monotonic() - start
                last_error = exc

            if attempt < self.config.retries:
                time.sleep(2 ** (attempt - 1))

        raise UploadError(
            f"Failed to upload {filepath.name} after {self.config.retries} attempt(s): {last_error}"
        )
