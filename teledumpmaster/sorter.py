# Natural (human-friendly) file sorting.
# "episode2" sorts before "episode10" by treating numeric parts as numbers.

from __future__ import annotations

import os
import re

# Regex splits "episode10part2" into ["episode", "10", "part", "2"]
_SPLIT_RE = re.compile(r"(\d+)")


def _sort_key(filename: str) -> list[str | int]:
    """Convert a filename into a sort key for natural ordering.

    Text parts are lowercased, numeric parts are converted to int so that
    "10" sorts after "2" instead of before it (as lexicographic order would).
    """
    parts: list[str | int] = []
    for chunk in _SPLIT_RE.split(filename):
        if not chunk:
            continue
        parts.append(int(chunk) if chunk.isdigit() else chunk.lower())
    return parts


def natural_sort(names: list[str]) -> list[str]:
    """Sort a list of filenames in natural, case-insensitive order."""
    return sorted(names, key=_sort_key)


def sort_paths(paths: list[str]) -> list[str]:
    """Sort file paths by their base filename (not the full path) in natural order."""
    return sorted(paths, key=lambda p: _sort_key(os.path.basename(p)))
