"""zettel_parser: A parser for a custom variant of Org-mode."""

from zettel_parser import regex
from zettel_parser.toplevel import (
    NodeProperty,
    PropertyDrawer,
    TopLevelElement,
    TopLevelParser,
    parse,
    parse_toplevel,
)

__version__ = "0.1.0"

__all__ = [
    "NodeProperty",
    "PropertyDrawer",
    "TopLevelElement",
    "TopLevelParser",
    "__version__",
    "parse",
    "parse_toplevel",
    "regex",
]
