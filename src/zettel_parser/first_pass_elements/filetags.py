"""File tags element produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from zettel_parser.common_regex import FILETAGS

if TYPE_CHECKING:
    from zettel_parser.cursor import Cursor


@dataclass
class FileTags:
    """A file tags keyword (#+filetags: :tag1:tag2: ...).

    Attributes:
        tags: The tags in order. Tags are case-sensitive and may contain
            spaces.
        raw_line: Verbatim source line comprising this keyword.
    """

    tags: list[str]
    raw_line: str = field(default="", compare=False)

    @classmethod
    def try_parse(cls, cursor: Cursor[str]) -> FileTags | None:
        """Consume a leading file tags keyword from ``cursor``.

        Args:
            cursor: The cursor to consume a line from.

        Returns:
            A FileTags instance, or None if the line is not a file tags keyword.
        """
        line = cursor.current
        if not isinstance(line, str):
            return None
        match = FILETAGS.match(line)
        if match is None:
            return None
        tags = [tag for tag in match.group("tags").split(":") if tag]
        cursor.advance()
        return cls(tags=tags, raw_line=line)

    def __str__(self) -> str:
        """Return the verbatim representation of the file tags line."""
        return self.raw_line
