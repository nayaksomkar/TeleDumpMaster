# Telegram Bot API uploader with retry, exponential backoff, and speed tracking.
# Uses the sendDocument method to upload files to a chat/channel.

from __future__ import annotations

import time
import uuid
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any

import requests

from .config import Config
from .exceptions import UploadError

API_BASE = "https://api.telegram.org/bot{token}/{method}"
_CHUNK_SIZE = 65536  # 64 KB per read — smooth progress updates without excessive overhead


class TelegramUploader:
    """Upload files to a Telegram chat via the Bot API with retry logic.

    Each upload attempt measures elapsed time so callers can report speed.
    On success the Telegram API response is returned as-is.
    """

    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()

    def _multipart_body(
        self,
        filepath: Path,
        fields: dict[str, str],
        boundary: str,
        on_bytes: Callable[[int], None] | None,
    ) -> Generator[bytes, None, None]:
        yield f"--{boundary}\r\n".encode()
        for key, value in fields.items():
            yield (
                f'Content-Disposition: form-data; name="{key}"\r\n'
                f"\r\n"
                f"{value}\r\n"
                f"--{boundary}\r\n"
            ).encode()
        yield (
            f'Content-Disposition: form-data; name="document"; filename="{filepath.name}"\r\n'
            f"Content-Type: application/octet-stream\r\n"
            f"\r\n"
        ).encode()
        with filepath.open("rb") as f:
            while True:
                chunk = f.read(_CHUNK_SIZE)
                if not chunk:
                    break
                yield chunk
                if on_bytes:
                    on_bytes(len(chunk))
        yield f"\r\n--{boundary}--\r\n".encode()

    def send_document(
        self,
        filepath: str | Path,
        caption: str | None = None,
        on_bytes: Callable[[int], None] | None = None,
    ) -> dict[str, Any]:
        """Upload a single file to Telegram.

        If on_bytes is provided, it is called with the number of bytes yielded
        to the HTTP layer (real-time during network send).

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
        file_size = filepath.stat().st_size

        for attempt in range(1, self.config.retries + 1):
            start = time.monotonic()
            try:
                boundary = uuid.uuid4().hex
                fields = {"chat_id": self.config.channel_id, "caption": caption or ""}
                body = self._multipart_body(filepath, fields, boundary, on_bytes)
                response = self.session.post(
                    API_BASE.format(token=self.config.bot_token, method="sendDocument"),
                    data=body,
                    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
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
