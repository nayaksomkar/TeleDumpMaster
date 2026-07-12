"""Tests for the natural sorter."""

from __future__ import annotations

from teledumpmaster.sorter import natural_sort, sort_paths


def test_natural_sort_numbers() -> None:
    names = ["episode10.mkv", "episode2.srt", "episode1.mkv"]
    assert natural_sort(names) == [
        "episode1.mkv",
        "episode2.srt",
        "episode10.mkv",
    ]


def test_natural_sort_case_insensitive() -> None:
    names = ["Movie.mp4", "movie.srt", "MOVIE.txt"]
    assert natural_sort(names) == ["Movie.mp4", "movie.srt", "MOVIE.txt"]


def test_natural_sort_mixed() -> None:
    names = ["Lesson10.pdf", "lesson2.pdf", "lesson1.txt"]
    assert natural_sort(names) == [
        "lesson1.txt",
        "lesson2.pdf",
        "Lesson10.pdf",
    ]


def test_sort_paths_uses_basename() -> None:
    paths = ["/a/episode2.mkv", "/b/episode10.mkv", "/c/episode1.mkv"]
    assert sort_paths(paths) == [
        "/c/episode1.mkv",
        "/a/episode2.mkv",
        "/b/episode10.mkv",
    ]
