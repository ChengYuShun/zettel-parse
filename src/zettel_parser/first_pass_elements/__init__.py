"""Element types produced by the first parsing pass."""

from __future__ import annotations

from zettel_parser.first_pass_elements.block import Block
from zettel_parser.first_pass_elements.filetags import FileTags
from zettel_parser.first_pass_elements.headline import Headline
from zettel_parser.first_pass_elements.latex_block import (
    LatexBlock,
    LatexBlockType,
)
from zettel_parser.first_pass_elements.list_item import ListItem, parse_checkbox
from zettel_parser.first_pass_elements.property_drawer import (
    NodeProperty,
    PropertyDrawer,
)
from zettel_parser.first_pass_elements.title import Title

FirstPassElement = (
    str
    | PropertyDrawer
    | Block
    | LatexBlock
    | Title
    | FileTags
    | Headline
    | ListItem
)

__all__ = [
    "Block",
    "FileTags",
    "FirstPassElement",
    "Headline",
    "LatexBlock",
    "LatexBlockType",
    "ListItem",
    "NodeProperty",
    "PropertyDrawer",
    "Title",
    "parse_checkbox",
]
