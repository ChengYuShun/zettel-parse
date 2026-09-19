"""A generic movable cursor shared by the first and structure passes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


@dataclass
class Cursor(Generic[T]):
    """A movable position over a sequence of elements.

    Attributes:
        elements: The elements being traversed.
        index: The current position within ``elements``.
    """

    elements: list[T]
    index: int = 0

    @property
    def at_end(self) -> bool:
        """Return True if the cursor has moved past the last element."""
        return self.index >= len(self.elements)

    @property
    def current(self) -> T | None:
        """Return the element at the cursor, or None if at the end."""
        return self.peek()

    def peek(self, offset: int = 0) -> T | None:
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
