"""Second (structure) pass over first-pass elements.

This module defines the cursor shared by the small parsers that make up the
structure pass.  Each parser consumes elements from a :class:`Cursor` and
produces a higher-level structure element.
"""

from __future__ import annotations

from dataclasses import dataclass

from zettel_parser.first_pass_elements import FirstPassElement


@dataclass
class Cursor:
    """A movable position over a sequence of first-pass elements.

    Attributes:
        elements: The first-pass elements being traversed.
        index: The current position within ``elements``.
    """

    elements: list[FirstPassElement]
    index: int = 0

    @property
    def at_end(self) -> bool:
        """Return True if the cursor has moved past the last element."""
        return self.index >= len(self.elements)

    @property
    def current(self) -> FirstPassElement | None:
        """Return the element at the cursor, or None if at the end."""
        return self.peek()

    def peek(self, offset: int = 0) -> FirstPassElement | None:
        """Return the element at ``index + offset`` without moving.

        Args:
            offset: The relative offset from the current position.

        Returns:
            The element, or None if the position is out of range.
        """
        position = self.index + offset
        if 0 <= position < len(self.elements):
            return self.elements[position]
        return None

    def advance(self, count: int = 1) -> None:
        """Move the cursor forward by ``count`` elements."""
        self.index += count


__all__ = ["Cursor"]
