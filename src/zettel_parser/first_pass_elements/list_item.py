"""List item element produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ListItem:
    """A plain list item line, ordered or unordered.

    Attributes:
        bullet: The list marker (``-``, ``+``, ``1.``, or ``1)`` with an
            arbitrary number).
        value: The item text following the marker.
        raw_line: Verbatim source line comprising this list item.
    """

    bullet: str
    value: str
    raw_line: str = field(default="", compare=False)

    @property
    def ordered(self) -> bool:
        """Return True if this is an ordered list item."""
        return self.bullet not in ("-", "+")

    def __str__(self) -> str:
        """Return the verbatim representation of the list item."""
        return self.raw_line
