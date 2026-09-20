"""First pass parser for custom Org-mode variant.

This module provides the first parsing pass that ingests an iterable of
lines or bytes and outputs a higher-level structure, including parsed
property drawers, blocks, LaTeX expressions, titles, file tags, headlines,
and list items.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from zettel_parser.cursor import Cursor
from zettel_parser.first_pass_elements import (
    Block,
    CheckboxState,
    FileTags,
    FirstPassElement,
    Headline,
    LatexBlock,
    LatexBlockType,
    ListItem,
    NodeProperty,
    PropertyDrawer,
    Title,
)

LineSource = Iterable[str | bytes] | str | bytes


class FirstPassParser:
    """First parsing pass over Org-mode documents.

    Consumes an iterable of lines or raw text/bytes and produces
    the parsed document structure containing lines, property drawers,
    blocks, LaTeX expressions, titles, file tags, headlines, and list items.
    """

    parsers: tuple[Callable[[Cursor[str]], FirstPassElement | None], ...] = (
        PropertyDrawer.try_parse,
        Block.try_parse,
        LatexBlock.try_parse,
        Title.try_parse,
        FileTags.try_parse,
        Headline.try_parse,
        ListItem.try_parse_toplevel,
    )

    def __init__(
        self,
        encoding: str = "utf-8",
        errors: str = "strict",
    ) -> None:
        # Encoding parameters used when decoding binary input streams.
        self.encoding = encoding
        self.errors = errors

    def _normalize_lines(self, source: LineSource) -> list[str]:
        # Convert heterogeneous input types (single str/bytes or an iterable of
        # chunks/lines) into a uniform list of text lines, preserving line endings.
        if isinstance(source, (str, bytes)):
            if isinstance(source, bytes):
                source = source.decode(self.encoding, errors=self.errors)
            return source.splitlines(keepends=True)

        lines: list[str] = []
        for line in source:
            # Decode binary items before inspection
            if isinstance(line, bytes):
                text = line.decode(self.encoding, errors=self.errors)
            elif isinstance(line, str):
                text = line
            else:
                raise TypeError(
                    f"Expected line to be str or bytes, got {type(line).__name__}"
                )
            # Split chunks with multiple lines; keep solitary empty lines intact
            if "\n" in text or "\r" in text:
                lines.extend(text.splitlines(keepends=True))
            else:
                lines.append(text)
        return lines

    def parse(self, source: LineSource) -> list[FirstPassElement]:
        """Parse source lines or bytes into higher-level structures."""
        cursor: Cursor[str] = Cursor(self._normalize_lines(source))
        result: list[FirstPassElement] = []

        while not cursor.at_end:
            # Try each element parser in turn; the first success consumes input.
            for parser in self.parsers:
                element = parser(cursor)
                if element is not None:
                    result.append(element)
                    break
            else:
                # Unrecognized lines are preserved verbatim.
                line = cursor.current
                assert line is not None
                result.append(line)
                cursor.advance()

        return result

    def __call__(self, source: LineSource) -> list[FirstPassElement]:
        # Allow parser instances to be invoked directly as callables.
        return self.parse(source)


class ListItemFirstPassParser(FirstPassParser):
    """First pass restricted to the content of a list item.

    Only blocks, nested list items, LaTeX blocks, and plain lines are
    recognized.  Other keywords and structures are preserved as plain lines.
    """

    parsers = (
        Block.try_parse,
        LatexBlock.try_parse,
        ListItem.try_parse_in_list,
    )


def parse_first_pass(
    source: LineSource,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> list[FirstPassElement]:
    """Parse an iterable of lines or bytes into a first-pass structure.

    Extracts property drawers, blocks, LaTeX expressions, titles, file tags,
    headlines, and list items while preserving other lines verbatim.
    """
    return FirstPassParser(encoding=encoding, errors=errors).parse(source)


__all__ = [
    "Block",
    "CheckboxState",
    "Cursor",
    "FileTags",
    "FirstPassElement",
    "FirstPassParser",
    "Headline",
    "LatexBlock",
    "LatexBlockType",
    "LineSource",
    "ListItem",
    "ListItemFirstPassParser",
    "NodeProperty",
    "PropertyDrawer",
    "Title",
    "parse_first_pass",
]
