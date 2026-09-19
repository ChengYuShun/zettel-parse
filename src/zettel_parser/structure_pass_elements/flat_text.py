"""Flat text element produced by the structure pass."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from zettel_parser.structure_pass_elements.blank_lines import BlankLines
from zettel_parser.structure_pass_elements.paragraph import Paragraph

if TYPE_CHECKING:
    from zettel_parser.first_pass_elements import FirstPassElement
    from zettel_parser.structure_pass import Cursor

FlatTextPart = Paragraph | BlankLines


@dataclass
class FlatText:
    """A run of paragraphs separated by blank lines.

    A flat text cannot begin with blank lines, but may end with them.  For
    ``n`` paragraphs it therefore contains either ``n - 1`` or ``n``
    BlankLines objects.

    Attributes:
        elements: The paragraphs and blank line runs, in order.
    """

    elements: list[FlatTextPart] = field(default_factory=list)

    @classmethod
    def try_parse(cls, cursor: Cursor[FirstPassElement]) -> FlatText | None:
        """Consume a leading flat text run from ``cursor``.

        Parsing starts only if the cursor is at a paragraph.  Paragraphs are
        then consumed together with the blank lines separating them, and any
        trailing blank lines.  Parsing stops at the first element that is
        neither, or at the end of the cursor.  If no paragraph starts at the
        cursor, it is left untouched and None is returned.

        Args:
            cursor: The cursor to consume elements from.

        Returns:
            A FlatText instance, or None if no flat text starts here.
        """
        first = Paragraph.try_parse(cursor)
        if first is None:
            return None

        elements: list[FlatTextPart] = [first]
        while True:
            blanks = BlankLines.try_parse(cursor)
            if blanks is None:
                break
            elements.append(blanks)
            paragraph = Paragraph.try_parse(cursor)
            if paragraph is None:
                break
            elements.append(paragraph)

        return cls(elements=elements)

    @property
    def paragraphs(self) -> list[Paragraph]:
        """Return the paragraphs contained in this flat text, in order."""
        return [
            element for element in self.elements if isinstance(element, Paragraph)
        ]

    def __str__(self) -> str:
        """Return the verbatim representation of the flat text."""
        return "".join(str(element) for element in self.elements)


__all__ = ["FlatText", "FlatTextPart"]
