from __future__ import annotations

import os
import re

_SPLIT_RE = re.compile(r"(\d+)")


def _sort_key(filename: str) -> list[str | int]:
    parts: list[str | int] = []
    for chunk in _SPLIT_RE.split(filename):
        if not chunk:
            continue
        parts.append(int(chunk) if chunk.isdigit() else chunk.lower())
    return parts


def natural_sort(names: list[str]) -> list[str]:
    return sorted(names, key=_sort_key)


def sort_paths(paths: list[str]) -> list[str]:
    return sorted(paths, key=lambda p: _sort_key(os.path.basename(p)))
