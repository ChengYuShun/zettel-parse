"""Zettel element produced by the structure pass."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from zettel_parser.first_pass_elements import (
    FileTags as FirstPassFileTags,
)
from zettel_parser.first_pass_elements import (
    Title as FirstPassTitle,
)
from zettel_parser.structure_pass_elements.node import Node

if TYPE_CHECKING:
    from zettel_parser.cursor import Cursor
    from zettel_parser.first_pass_elements import FirstPassElement


@dataclass
class Zettel(Node):
    """The root node of a document, i.e. a headline of level 0.

    Attributes:
        filetags: The file tags declared by ``#+filetags`` keywords.
    """

    filetags: str = ""

    @classmethod
    def try_parse(cls, cursor: Cursor[FirstPassElement]) -> Zettel:
        """Consume a document's preamble and headlines from ``cursor``.

        The preamble is an optional property drawer, followed by any number of
        ``#+title`` and ``#+filetags`` keywords (later occurrences override
        earlier ones).  The rest is parsed like a level-0 headline: a
        :class:`FlatText` body followed by the nested headlines.

        Args:
            cursor: The cursor to consume elements from.

        Returns:
            A Zettel describing the whole document (possibly empty).
        """
        properties = cls._parse_property_drawer(cursor)

        title = ""
        filetags = ""
        while True:
            current = cursor.current
            if isinstance(current, FirstPassTitle):
                title = current.value
                cursor.advance()
            elif isinstance(current, FirstPassFileTags):
                filetags = current.tags
                cursor.advance()
            else:
                break

        body, children = cls._parse_body_and_children(cursor, 0)
        return cls(
            title=title,
            level=0,
            properties=properties,
            body=body,
            children=children,
            filetags=filetags,
        )


__all__ = ["Zettel"]
