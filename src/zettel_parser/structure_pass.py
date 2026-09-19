"""Second (structure) pass over first-pass elements.

This module exposes the cursor shared by the small parsers that make up the
structure pass.  Each parser consumes elements from a :class:`Cursor` and
produces a higher-level structure element.
"""

from __future__ import annotations

from zettel_parser.cursor import Cursor

__all__ = ["Cursor"]
