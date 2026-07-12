from __future__ import annotations

import argparse
import logging
import sys
from typing import Any

from . import __version__
from .config import Config
from .exceptions import ConfigurationError, TeleDumpMasterError
from .logging_utils import UploadRecorder, setup_logging
from .watcher import Watcher


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="teledumpmaster",
        description="Watch a folder and upload files to Telegram in sorted order.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--once",
        action="store_true",
        help="scan and upload pending files once, then exit",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="console log verbosity (default: INFO)",
    )
    parser.add_argument(
        "--dotenv",
        default=None,
        help="path to a .env file (defaults to ./.env)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    setup_logging(level=getattr(logging, args.log_level))

    try:
        config = Config.from_env(dotenv_path=args.dotenv)
    except ConfigurationError as exc:
        logging.error("Configuration error: %s", exc)
        return 2

    recorder = UploadRecorder(config.log_dir, config.log_format)
    watcher = Watcher(config)

    def on_upload(filepath: str, result: dict[str, Any]) -> None:
        recorder.record(filepath, result)

    try:
        if args.once:
            uploaded = watcher.process_once(on_upload=on_upload)
            logging.info("Done. Uploaded %d file(s).", uploaded)
            return 0
        watcher.run_forever(on_upload=on_upload)
        return 0
    except TeleDumpMasterError as exc:
        logging.error("Error: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
