"""Blank line run element produced by the structure pass."""

from __future__ import annotations

from dataclasses import dataclass

from zettel_parser.common_regex import BLANK_LINE
from zettel_parser.cursor import Cursor
from zettel_parser.first_pass_elements import FirstPassElement


@dataclass
class BlankLines:
    """A run of one or more consecutive blank lines.

    Attributes:
        text: The verbatim blank lines, concatenated in order.
    """

    text: str = ""

    @property
    def count(self) -> int:
        """Return the number of blank lines in the run."""
        return len(self.text.splitlines())

    @classmethod
    def try_parse(cls, cursor: Cursor[FirstPassElement]) -> BlankLines | None:
        """Consume a leading run of blank lines from ``cursor``.

        Leading verbatim string elements that consist solely of spaces and
        tabs are consumed.  If no blank line is found, the cursor is left
        untouched and None is returned.

        Args:
            cursor: The cursor to consume elements from.

        Returns:
            A BlankLines instance, or None if the cursor is not at a blank line.
        """
        lines: list[str] = []
        while isinstance(element := cursor.peek(), str) and BLANK_LINE.match(
            element
        ):
            lines.append(element)
            cursor.advance()
        if not lines:
            return None
        return cls(text="".join(lines))

    def __str__(self) -> str:
        """Return the verbatim representation of the blank lines."""
        return self.text


__all__ = ["BlankLines"]
