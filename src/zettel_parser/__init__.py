"""zettel_parser: A parser for a custom variant of Org-mode."""

from zettel_parser import common_regex, first_pass, inline_pass, structure_pass
from zettel_parser.first_pass import parse_first_pass
from zettel_parser.inline_pass import parse_inline
from zettel_parser.structure_pass import (
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
    parse,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "BlankLines",
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
    "common_regex",
    "first_pass",
    "inline_pass",
    "structure_pass",
    "parse",
    "parse_first_pass",
    "parse_inline",
]
