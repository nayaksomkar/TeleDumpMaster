# Telegram Bot API uploader with retry, exponential backoff, and speed tracking.
# Uses the sendDocument method to upload files to a chat/channel.

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import requests

from .config import Config
from .exceptions import UploadError

API_BASE = "https://api.telegram.org/bot{token}/{method}"


class TelegramUploader:
    """Upload files to a Telegram chat via the Bot API with retry logic.

    Each upload attempt measures elapsed time so callers can report speed.
    On success the Telegram API response is returned as-is.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        # Reuse a session for connection pooling (faster repeated uploads)
        self.session = requests.Session()

    def send_document(self, filepath: str | Path, caption: str | None = None) -> dict[str, Any]:
        """Upload a single file to Telegram.

        Retries on transient failures using exponential backoff (1s, 2s, 4s…).
        Returns the Telegram API response dict, which includes file size info
        and the server's message_id on success.

        Raises UploadError if all attempts fail.
        """
        filepath = Path(filepath)
        caption = caption if caption is not None else self.config.caption
        if caption == "__FILENAME__":
            caption = filepath.name
        last_error: Exception | None = None
        file_size = filepath.stat().st_size  # bytes

        for attempt in range(1, self.config.retries + 1):
            start = time.monotonic()
            try:
                with filepath.open("rb") as handle:
                    response = self.session.post(
                        API_BASE.format(token=self.config.bot_token, method="sendDocument"),
                        data={"chat_id": self.config.channel_id, "caption": caption or ""},
                        files={"document": (filepath.name, handle)},
                        timeout=self.config.timeout,
                    )
                elapsed = time.monotonic() - start
                payload: dict[str, Any] = response.json()

                if response.status_code == 200 and payload.get("ok"):
                    # Enrich the response with timing and size metadata
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

            # Wait before retrying: 1s after attempt 1, 2s after attempt 2, etc.
            if attempt < self.config.retries:
                time.sleep(2 ** (attempt - 1))

        raise UploadError(
            f"Failed to upload {filepath.name} after {self.config.retries} attempt(s): {last_error}"
        )
