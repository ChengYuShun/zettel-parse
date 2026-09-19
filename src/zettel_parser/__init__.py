"""zettel_parser: A parser for a custom variant of Org-mode."""

from zettel_parser import common_regex
from zettel_parser.toplevel import (
    Block,
    LatexBlock,
    LatexBlockType,
    NodeProperty,
    PropertyDrawer,
    TopLevelElement,
    TopLevelParser,
    parse,
    parse_toplevel,
)

__version__ = "0.1.0"

__all__ = [
    "Block",
    "LatexBlock",
    "LatexBlockType",
    "NodeProperty",
    "PropertyDrawer",
    "TopLevelElement",
    "TopLevelParser",
    "__version__",
    "common_regex",
    "parse",
    "parse_toplevel",
]
