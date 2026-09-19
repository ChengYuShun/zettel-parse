"""List element produced by the structure pass."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from zettel_parser.structure_pass_elements.blank_lines import BlankLines
from zettel_parser.structure_pass_elements.list_item import ListItem

if TYPE_CHECKING:
    from zettel_parser.first_pass_elements import FirstPassElement
    from zettel_parser.structure_pass import Cursor

ListPart = ListItem | BlankLines


def _bullet_type(bullet: str) -> str:
    """Return the type of a bullet, ignoring ordered-item values.

    Ordered bullets (e.g. ``1.`` and ``3.``) share the type of their
    delimiter, so non-consecutive numbers still belong to the same list.
    """
    if bullet.endswith((".", ")")):
        return bullet[-1]
    return bullet


@dataclass
class List:
    """A run of list items sharing the same bullet type.

    Items may be separated by blank line runs, but a list never ends with
    one: trailing blank lines are left for the surrounding parser.  Individual
    items are available through the :attr:`items` property, indexing, and
    iteration.

    Attributes:
        elements: The list items and blank line runs, in order.
    """

    elements: list[ListPart] = field(default_factory=list)

    @classmethod
    def try_parse(cls, cursor: Cursor[FirstPassElement]) -> List | None:
        """Consume a leading list from ``cursor``.

        Parsing starts only if the cursor is at a first-pass list item.  Every
        following list item of the same bullet type is consumed, together with
        the blank line runs separating them.  A blank line run is only consumed
        when a matching list item follows it; trailing blank lines, or blank
        lines before a different bullet type, are left in place.  If no list
        item starts at the cursor, it is left untouched and None is returned.

        Args:
            cursor: The cursor to consume elements from.

        Returns:
            A List instance, or None if no list starts here.
        """
        first = ListItem.try_parse(cursor)
        if first is None:
            return None

        bullet_type = _bullet_type(first.bullet)
        elements: list[ListPart] = [first]

        while True:
            saved = cursor.index
            blanks = BlankLines.try_parse(cursor)
            item = ListItem.try_parse(cursor)
            if item is None or _bullet_type(item.bullet) != bullet_type:
                cursor.index = saved
                break
            if blanks is not None:
                elements.append(blanks)
            elements.append(item)

        return cls(elements=elements)

    @property
    def items(self) -> list[ListItem]:
        """Return the list items contained in this list, in order."""
        return [
            element for element in self.elements if isinstance(element, ListItem)
        ]

    @property
    def bullet_type(self) -> str:
        """Return the shared bullet type of this list."""
        items = self.items
        return _bullet_type(items[0].bullet) if items else ""

    def __getitem__(self, index: int) -> ListItem:
        """Return the nth list item."""
        return self.items[index]

    def __len__(self) -> int:
        """Return the number of list items."""
        return sum(
            1 for element in self.elements if isinstance(element, ListItem)
        )

    def __iter__(self) -> Iterator[ListItem]:
        """Iterate over the list items."""
        return iter(self.items)

    def __str__(self) -> str:
        """Return the verbatim representation of the list."""
        return "".join(str(element) for element in self.elements)


__all__ = ["List", "ListPart"]
