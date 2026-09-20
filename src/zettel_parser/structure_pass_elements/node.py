"""Base node element produced by the structure pass."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from zettel_parser.cursor import Cursor
from zettel_parser.first_pass_elements import (
    FirstPassElement,
    PropertyDrawer,
)
from zettel_parser.first_pass_elements import (
    Headline as FirstPassHeadline,
)
from zettel_parser.structure_pass_elements.flat_text import FlatText

if TYPE_CHECKING:
    # ``Headline`` is a subclass of ``Node``, so it cannot be imported at
    # runtime here.  The reference below is a forward reference resolved by the
    # type checker, and ``Headline`` is imported locally where it is needed.
    from zettel_parser.structure_pass_elements.headline import Headline


@dataclass
class Node:
    """State shared by :class:`Headline` and :class:`Zettel`.

    Attributes:
        title: The node title (headline text, or the ``#+title`` value).
        level: The outline level; always ``0`` for a Zettel.
        properties: The property drawer immediately following the node, if any.
        body: The node content parsed as flat text, if any.
        children: The nested headlines belonging to this node, in order.
    """

    title: str = ""
    level: int = 0
    properties: PropertyDrawer | None = None
    body: FlatText | None = None
    children: list[Headline] = field(default_factory=list)

    @staticmethod
    def _parse_property_drawer(
        cursor: Cursor[FirstPassElement],
    ) -> PropertyDrawer | None:
        """Consume an immediately following property drawer, if present."""
        if isinstance(cursor.current, PropertyDrawer):
            drawer = cursor.current
            cursor.advance()
            return drawer
        return None

    @staticmethod
    def _parse_body_and_children(
        cursor: Cursor[FirstPassElement],
        level: int,
    ) -> tuple[FlatText | None, list[Headline]]:
        """Parse a node's flat-text body followed by its nested headlines.

        Headlines are collected while their level is greater than ``level``;
        the first headline at or above ``level`` is left for the caller.
        """
        from zettel_parser.structure_pass_elements.headline import Headline

        body = FlatText.try_parse(cursor)
        children: list[Headline] = []
        while True:
            current = cursor.current
            if not isinstance(current, FirstPassHeadline) or current.level <= level:
                break
            child = Headline.try_parse(cursor)
            assert child is not None
            children.append(child)
        return body, children


__all__ = ["Node"]
