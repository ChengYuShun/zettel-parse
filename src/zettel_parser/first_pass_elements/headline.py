"""Headline element produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from zettel_parser.common_regex import HEADLINE

if TYPE_CHECKING:
    from zettel_parser.cursor import Cursor


@dataclass
class Headline:
    """An Org-mode headline (one or more leading stars and a title).

    Attributes:
        level: The outline level, i.e. the number of leading stars.
        title: The headline text after the stars.
        raw_line: Verbatim source line comprising this headline.
    """

    level: int
    title: str
    raw_line: str = field(default="", compare=False)

    @classmethod
    def try_parse(cls, cursor: Cursor[str]) -> Headline | None:
        """Consume a leading headline from ``cursor``.

        Args:
            cursor: The cursor to consume a line from.

        Returns:
            A Headline instance, or None if the line is not a headline.
        """
        line = cursor.current
        if not isinstance(line, str):
            return None
        match = HEADLINE.match(line)
        if match is None:
            return None
        cursor.advance()
        return cls(
            level=len(match.group("stars")),
            title=match.group("title"),
            raw_line=line,
        )

    def __str__(self) -> str:
        """Return the verbatim representation of the headline."""
        return self.raw_line
