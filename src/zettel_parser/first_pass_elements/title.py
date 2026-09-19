"""Title element produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass, field

from zettel_parser.common_regex import TITLE
from zettel_parser.cursor import Cursor


@dataclass
class Title:
    """A document title keyword (#+title: ...).

    Attributes:
        value: The title text following the keyword.
        raw_line: Verbatim source line comprising this title.
    """

    value: str
    raw_line: str = field(default="", compare=False)

    @classmethod
    def try_parse(cls, cursor: Cursor[str]) -> Title | None:
        """Consume a leading title keyword from ``cursor``.

        Args:
            cursor: The cursor to consume a line from.

        Returns:
            A Title instance, or None if the line is not a title keyword.
        """
        line = cursor.current
        if not isinstance(line, str):
            return None
        match = TITLE.match(line)
        if match is None:
            return None
        cursor.advance()
        return cls(value=match.group("value"), raw_line=line)

    def __str__(self) -> str:
        """Return the verbatim representation of the title line."""
        return self.raw_line
