"""Blank line run element produced by the structure pass."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from zettel_parser.common_regex import BLANK_LINE

if TYPE_CHECKING:
    from zettel_parser.structure_pass import Cursor


@dataclass
class BlankLines:
    """A run of one or more consecutive blank lines.

    Attributes:
        raw_lines: The verbatim blank source lines, in order.
    """

    raw_lines: list[str] = field(default_factory=list, compare=False)

    @classmethod
    def try_parse(cls, cursor: Cursor) -> BlankLines | None:
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
        return cls(raw_lines=lines)

    def __str__(self) -> str:
        """Return the verbatim representation of the blank lines."""
        return "".join(self.raw_lines)


__all__ = ["BlankLines"]
