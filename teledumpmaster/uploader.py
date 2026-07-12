from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import requests

from .config import Config
from .exceptions import UploadError

API_BASE = "https://api.telegram.org/bot{token}/{method}"


class TelegramUploader:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.session = requests.Session()

    def send_document(self, filepath: str | Path, caption: str | None = None) -> dict[str, Any]:
        filepath = Path(filepath)
        caption = caption if caption is not None else self.config.caption
        last_error: Exception | None = None

        for attempt in range(1, self.config.retries + 1):
            try:
                with filepath.open("rb") as handle:
                    response = self.session.post(
                        API_BASE.format(
                            token=self.config.bot_token, method="sendDocument"
                        ),
                        data={
                            "chat_id": self.config.channel_id,
                            "caption": caption or "",
                        },
                        files={"document": (filepath.name, handle)},
                        timeout=self.config.timeout,
                    )
                payload: dict[str, Any] = response.json()
                if response.status_code == 200 and payload.get("ok"):
                    return payload
                last_error = UploadError(
                    f"Telegram API error: {payload.get('description', response.text)}"
                )
            except requests.RequestException as exc:
                last_error = exc

            if attempt < self.config.retries:
                time.sleep(2 ** (attempt - 1))

        raise UploadError(
            f"Failed to upload {filepath.name} after {self.config.retries} attempt(s): "
            f"{last_error}"
        )
