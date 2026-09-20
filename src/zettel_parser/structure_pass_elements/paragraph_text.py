"""Paragraph text element produced by the structure pass."""

from __future__ import annotations

from dataclasses import dataclass

from zettel_parser.common_regex import BLANK_LINE
from zettel_parser.cursor import Cursor
from zettel_parser.first_pass_elements import FirstPassElement


@dataclass
class ParagraphText:
    """A run of consecutive non-blank text lines, concatenated verbatim.

    Attributes:
        text: The concatenated source lines, in order.
    """

    text: str = ""

    @classmethod
    def try_parse(cls, cursor: Cursor[FirstPassElement]) -> ParagraphText | None:
        """Consume a leading run of non-blank text lines from ``cursor``.

        Consecutive verbatim string elements are consumed until a blank line or
        a non-string element is reached, or the cursor is exhausted.  The lines
        are concatenated unmodified.  If the cursor does not start at a
        non-blank text line, it is left untouched and None is returned.

        Args:
            cursor: The cursor to consume elements from.

        Returns:
            A ParagraphText instance, or None if no text run starts here.
        """
        lines: list[str] = []
        while isinstance(element := cursor.peek(), str) and not BLANK_LINE.match(
            element
        ):
            lines.append(element)
            cursor.advance()
        if not lines:
            return None
        return cls(text="".join(lines))

    def __str__(self) -> str:
        """Return the concatenated text."""
        return self.text


__all__ = ["ParagraphText"]
