"""Paragraph element produced by the structure pass."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from zettel_parser.common_regex import BLANK_LINE
from zettel_parser.first_pass_elements import Block, FirstPassElement, LatexBlock

if TYPE_CHECKING:
    from zettel_parser.structure_pass import Cursor


@dataclass
class Paragraph:
    """A sequence of text lines, LaTeX blocks, and blocks.

    Attributes:
        elements: The first-pass elements comprising this paragraph, in order.
    """

    elements: list[FirstPassElement] = field(default_factory=list)

    @classmethod
    def try_parse(cls, cursor: Cursor[FirstPassElement]) -> Paragraph | None:
        """Consume a leading paragraph from ``cursor``.

        A paragraph is a maximal run of non-blank lines, LaTeX blocks, and
        blocks.  Parsing stops at the first element that is none of these, or
        at a blank line.  If the cursor is not at the start of a paragraph,
        it is left untouched and None is returned.

        Args:
            cursor: The cursor to consume elements from.

        Returns:
            A Paragraph instance, or None if no paragraph starts here.
        """
        elements: list[FirstPassElement] = []
        while (element := cursor.peek()) is not None:
            if isinstance(element, str):
                if BLANK_LINE.match(element):
                    break
            elif not isinstance(element, (Block, LatexBlock)):
                break
            elements.append(element)
            cursor.advance()
        if not elements:
            return None
        return cls(elements=elements)

    def __str__(self) -> str:
        """Return the verbatim representation of the paragraph."""
        return "".join(str(element) for element in self.elements)


__all__ = ["Paragraph"]
