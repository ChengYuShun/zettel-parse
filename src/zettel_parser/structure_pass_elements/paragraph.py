"""Paragraph element produced by the structure pass."""

from __future__ import annotations

from dataclasses import dataclass, field

from zettel_parser.common_regex import BLANK_LINE
from zettel_parser.cursor import Cursor
from zettel_parser.first_pass_elements import Block, FirstPassElement, LatexBlock
from zettel_parser.structure_pass_elements.list import List


@dataclass
class Paragraph:
    """A sequence of text lines, LaTeX blocks, blocks, and lists.

    The items are consecutive: a blank line terminates the paragraph.  A list
    may itself contain blank lines; those are internal to the list and do not
    terminate the paragraph.

    Attributes:
        elements: The items comprising this paragraph, in order.
    """

    elements: list[FirstPassElement | List] = field(default_factory=list)

    @classmethod
    def try_parse(cls, cursor: Cursor[FirstPassElement]) -> Paragraph | None:
        """Consume a leading paragraph from ``cursor``.

        A paragraph is a maximal run of non-blank lines, LaTeX blocks, blocks,
        and lists.  List items are grouped into :class:`List` objects by
        delegating to :meth:`List.try_parse`.  Parsing stops at the first
        element that is none of these, or at a blank line.  If the cursor is
        not at the start of a paragraph, it is left untouched and None is
        returned.

        Args:
            cursor: The cursor to consume elements from.

        Returns:
            A Paragraph instance, or None if no paragraph starts here.
        """
        elements: list[FirstPassElement | List] = []
        while (element := cursor.peek()) is not None:
            lst = List.try_parse(cursor)
            if lst is not None:
                elements.append(lst)
                continue
            if isinstance(element, str):
                if BLANK_LINE.match(element):
                    break
            elif not isinstance(element, (Block, LatexBlock, List)):
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
