# CLI entry point — beautiful Rich-powered progress bar and styled output.

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

from . import __version__
from .config import Config
from .exceptions import ConfigurationError, TeleDumpMasterError
from .logging_utils import UploadRecorder, setup_logging
from .watcher import Watcher, _format_size, _format_speed

console = Console()


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with all CLI flags."""
    parser = argparse.ArgumentParser(
        prog="teledumpmaster",
        description="Watch a folder and upload files to Telegram in naturally sorted order.",
        epilog=(
            "Examples:\n"
            "  teledumpmaster                     Watch folder forever\n"
            "  teledumpmaster --once              Upload everything and exit\n"
            "  teledumpmaster --dry-run           Show what would be uploaded\n"
            "  teledumpmaster --no-progress       Run without progress bar (for CI/logs)\n"
            "  teledumpmaster --log-level DEBUG   Verbose output for debugging\n"
            "  teledumpmaster --caption              Use filename as caption\n"
            "  teledumpmaster --caption \"My caption\"  Custom caption for all files\n"
            "  teledumpmaster --dotenv /path/to/.env  Use a custom config file\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    parser.add_argument(
        "--once", action="store_true",
        help="scan and upload pending files once, then exit (useful for cron jobs)",
    )

    parser.add_argument(
        "--dry-run", action="store_true",
        help="scan and list files that would be uploaded, without actually uploading",
    )

    parser.add_argument(
        "--no-progress", action="store_true",
        help="disable the progress bar (useful for logs/CI)",
    )

    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="set console log verbosity (default: INFO)",
    )

    parser.add_argument(
        "--caption", nargs="?", const="__FILENAME__", default=None, metavar="TEXT",
        help="caption sent with every file (use without value to caption with filename)",
    )

    parser.add_argument(
        "--dotenv", default=None, metavar="PATH",
        help="path to a custom .env file (defaults to ./.env)",
    )

    return parser


def _run_dry_run(watcher: Watcher) -> int:
    """List files that would be uploaded without uploading them."""
    logging.info("Scanning folder: %s", watcher.config.upload_folder)
    files = watcher.scan()
    if files:
        console.print(f"\n[bold]Files found: {len(files)}[/]\n")
        for f in files:
            fpath = Path(f)
            size = _format_size(fpath.stat().st_size)
            console.print(f"  [cyan]•[/] [bold]{fpath.name}[/]  ([dim]{size}[/])")
        console.print()
    else:
        console.print("[yellow]No files to upload.[/]")
    return 0


def _run_with_progress(watcher: Watcher, on_upload: Any) -> dict[str, Any]:
    """Run once with a beautiful Rich progress bar."""
    columns = [
        TextColumn("[bold blue]Uploading", justify="right"),
        BarColumn(bar_width=40),
        TaskProgressColumn(),
        TextColumn("[bold]{task.fields[name]}"),
        TextColumn("[dim]({task.fields[size]} @ {task.fields[speed]})[/]"),
        TimeElapsedColumn(),
        TextColumn("<"),
        TimeRemainingColumn(),
    ]

    files = [f for f in watcher.scan() if f not in watcher._uploaded]
    total = len(files)

    if total == 0:
        return {"files": 0, "total_size": 0, "total_time": 0, "avg_speed": 0}

    with Progress(*columns, console=console) as progress:
        task = progress.add_task("", total=total, name="", size="", speed="")

        def on_progress(state: dict[str, Any]) -> None:
            size_str = _format_size(state["size"])
            speed_str = _format_speed(state["size"], state["elapsed"])
            progress.update(
                task,
                advance=1,
                name=state["file"],
                size=size_str,
                speed=speed_str,
            )
            action_tag = ""
            if state.get("action") == "deleted":
                action_tag = " [red](deleted)[/]"
            elif state.get("action") == "archived":
                action_tag = " [yellow](archived)[/]"
            label = f"[bold]{state['file']}[/]  ([dim]{size_str} @ {speed_str}[/]){action_tag}"
            console.print(f"  [green]✓[/] {label}")

        return watcher.process_once(on_upload=on_upload, on_progress=on_progress)


def _run_plain(watcher: Watcher, on_upload: Any) -> dict[str, Any]:
    """Run once without any progress bar (plain logging)."""
    return watcher.process_once(on_upload=on_upload)


def main(argv: list[str] | None = None) -> int:
    """Parse CLI args, load config, and start the watcher."""
    args = build_parser().parse_args(argv)
    setup_logging(level=getattr(logging, args.log_level))

    try:
        config = Config.from_env(dotenv_path=args.dotenv)
    except ConfigurationError as exc:
        logging.error("Configuration error: %s", exc)
        return 2

    if args.caption is not None:
        config.caption = args.caption

    watcher = Watcher(config)
    recorder = UploadRecorder(config.log_dir, config.log_format)

    def on_upload(filepath: str, result: dict[str, Any]) -> None:
        recorder.record(filepath, result)

    if args.dry_run:
        return _run_dry_run(watcher)

    try:
        if args.once:
            logging.info("Scanning folder: %s", config.upload_folder)
            if args.no_progress:
                summary = _run_plain(watcher, on_upload)
            else:
                summary = _run_with_progress(watcher, on_upload)

            if summary["files"]:
                console.print(
                    f"\n[bold green]Done![/] Uploaded [bold]{summary['files']}[/] file(s), "
                    f"[bold]{_format_size(summary['total_size'])}[/] total, "
                    f"avg [bold]{_format_speed(summary['total_size'], summary['total_time'])}[/], "
                    f"in [bold]{summary['total_time']:.1f}s[/]"
                )
            else:
                console.print("[yellow]No files to upload.[/]")
            return 0

        watcher.run_forever(on_upload=on_upload)
        return 0

    except TeleDumpMasterError as exc:
        logging.error("Error: %s", exc)
        return 1
    except KeyboardInterrupt:
        logging.info("Stopped by user")
        return 0


if __name__ == "__main__":
    sys.exit(main())
