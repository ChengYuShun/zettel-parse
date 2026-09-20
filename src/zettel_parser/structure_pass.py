"""Second (structure) pass over first-pass elements.

This module exposes the cursor shared by the small parsers that make up the
structure pass, along with the :func:`parse` entry point that runs an input
document through both passes and returns the resulting AST.
"""

from __future__ import annotations

from zettel_parser.cursor import Cursor
from zettel_parser.first_pass import LineSource, parse_first_pass
from zettel_parser.structure_pass_elements import (
    BlankLines,
    FlatText,
    FlatTextPart,
    Headline,
    List,
    ListItem,
    ListPart,
    Node,
    Paragraph,
    ParagraphPart,
    ParagraphText,
    Zettel,
)


def parse(
    source: LineSource,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> Zettel:
    """Parse a document into its structure-pass AST.

    The source is first run through the first pass and then through the
    structure pass, yielding a :class:`Zettel` describing the whole document.

    Args:
        source: The document to parse, as text, bytes, or an iterable of
            lines/chunks.
        encoding: The encoding used to decode binary input.
        errors: The error handling scheme used to decode binary input.

    Returns:
        A Zettel describing the whole document.
    """
    elements = parse_first_pass(source, encoding=encoding, errors=errors)
    return Zettel.try_parse(Cursor(elements))


__all__ = [
    "BlankLines",
    "Cursor",
    "FlatText",
    "FlatTextPart",
    "Headline",
    "List",
    "ListItem",
    "ListPart",
    "Node",
    "Paragraph",
    "ParagraphPart",
    "ParagraphText",
    "Zettel",
    "parse",
]
