"""Bookmark Tasks."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass
class BookmarkTask:
    """Bookmark Base Class."""


@dataclass
class BookmarkUpdateTask(BookmarkTask):
    """Bookmark a page."""

    auth_filter: Mapping[str, int | str | None]
    comic_pks: tuple[int]
    updates: Mapping[str, Any]


@dataclass
class UserActiveTask(BookmarkTask):
    """Update the user's last active status."""

    pk: int
