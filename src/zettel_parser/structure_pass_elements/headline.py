"""Headline element produced by the structure pass."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from zettel_parser.first_pass_elements import Headline as FirstPassHeadline
from zettel_parser.structure_pass_elements.node import Node

if TYPE_CHECKING:
    from zettel_parser.cursor import Cursor
    from zettel_parser.first_pass_elements import FirstPassElement


@dataclass
class Headline(Node):
    """A headline, optionally with a property drawer, body, and children."""

    @classmethod
    def try_parse(cls, cursor: Cursor[FirstPassElement]) -> Headline | None:
        """Consume a leading headline and its subtree from ``cursor``.

        The headline line is followed by an optional property drawer (only if
        it comes immediately after), a :class:`FlatText` body, and the nested
        headlines with a greater level.  Parsing stops at the first headline
        whose level is less than or equal to this headline's.  If the cursor is
        not at a headline, it is left untouched and None is returned.

        Args:
            cursor: The cursor to consume elements from.

        Returns:
            A Headline instance, or None if no headline starts here.
        """
        source = cursor.current
        if not isinstance(source, FirstPassHeadline):
            return None
        cursor.advance()

        properties = cls._parse_property_drawer(cursor)
        body, children = cls._parse_body_and_children(cursor, source.level)
        return cls(
            title=source.title,
            level=source.level,
            properties=properties,
            body=body,
            children=children,
        )


__all__ = ["Headline"]
