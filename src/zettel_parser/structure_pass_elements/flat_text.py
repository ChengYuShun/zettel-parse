"""Flat text element produced by the structure pass."""

from __future__ import annotations

from dataclasses import dataclass, field

from zettel_parser.cursor import Cursor
from zettel_parser.first_pass_elements import FirstPassElement
from zettel_parser.structure_pass_elements.blank_lines import BlankLines
from zettel_parser.structure_pass_elements.paragraph import Paragraph

FlatTextPart = Paragraph | BlankLines


@dataclass
class FlatText:
    """A run of paragraphs and blank line runs.

    A flat text is a maximal run of paragraphs and blank lines.  It may both
    begin and end with blank lines, so ``n`` paragraphs may be accompanied by
    up to ``n + 1`` BlankLines objects.

    Attributes:
        elements: The paragraphs and blank line runs, in order.
    """

    elements: list[FlatTextPart] = field(default_factory=list)

    @classmethod
    def try_parse(cls, cursor: Cursor[FirstPassElement]) -> FlatText | None:
        """Consume a leading flat text run from ``cursor``.

        Blank lines and paragraphs are consumed until an element that is
        neither is reached, or the cursor is exhausted.  Blank lines may lead,
        separate, and trail the paragraphs.  If the cursor starts at something
        other than a blank line or paragraph, it is left untouched and None is
        returned.

        Args:
            cursor: The cursor to consume elements from.

        Returns:
            A FlatText instance, or None if no flat text starts here.
        """
        elements: list[FlatTextPart] = []
        while True:
            blanks = BlankLines.try_parse(cursor)
            if blanks is not None:
                elements.append(blanks)
                continue
            paragraph = Paragraph.try_parse(cursor)
            if paragraph is not None:
                elements.append(paragraph)
                continue
            break

        if not elements:
            return None
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
