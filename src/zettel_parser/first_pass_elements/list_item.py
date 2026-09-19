"""List item element produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass, field

from zettel_parser.common_regex import LIST_ITEM
from zettel_parser.cursor import Cursor


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

    @classmethod
    def try_parse(cls, cursor: Cursor[str]) -> ListItem | None:
        """Consume a leading, unindented list item from ``cursor``.

        Indented list items are left for the structure pass and therefore
        return None here.

        Args:
            cursor: The cursor to consume a line from.

        Returns:
            A ListItem instance, or None if the line is not a list item.
        """
        line = cursor.current
        if not isinstance(line, str):
            return None
        match = LIST_ITEM.match(line)
        if match is None or match.group("indent"):
            return None
        cursor.advance()
        return cls(
            bullet=match.group("bullet"),
            value=match.group("value") or "",
            raw_line=line,
        )

    def __str__(self) -> str:
        """Return the verbatim representation of the list item."""
        return self.raw_line
