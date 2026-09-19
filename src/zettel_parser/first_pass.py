"""First pass parser for custom Org-mode variant.

This module provides the first parsing pass that ingests an iterable of
lines or bytes and outputs a higher-level structure, including parsed
property drawers, blocks, LaTeX expressions, titles, file tags, headlines,
and list items.
"""

from __future__ import annotations

from collections.abc import Iterable

from zettel_parser.common_regex import (
    BLOCK_BEGIN,
    BLOCK_END,
    FILETAGS,
    HEADLINE,
    LATEX_BLOCK_BEGIN,
    LATEX_BLOCK_END,
    LATEX_DELIMITERS,
    LIST_ITEM,
    NODE_PROPERTY,
    PROPERTY_DRAWER_BEGIN,
    PROPERTY_DRAWER_END,
    TITLE,
)
from zettel_parser.first_pass_elements import (
    Block,
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
from zettel_parser.first_pass_elements.latex_block import (
    LATEX_BLOCK_TYPE_BY_DELIMITER,
)

LineSource = Iterable[str | bytes] | str | bytes


class FirstPassParser:
    """First parsing pass over Org-mode documents.

    Consumes an iterable of lines or raw text/bytes and produces
    the parsed document structure containing lines, property drawers,
    blocks, LaTeX expressions, titles, file tags, headlines, and list items.
    """

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
        raw_lines = self._normalize_lines(source)
        result: list[FirstPassElement] = []
        i = 0
        n = len(raw_lines)

        # Scan lines sequentially, checking for property drawer boundaries.
        while i < n:
            line = raw_lines[i]
            if PROPERTY_DRAWER_BEGIN.match(line):
                drawer_lines = [line]
                j = i + 1
                found_end = False
                all_properties = True

                # Lookahead to find matching :END: and verify all intermediate
                # lines are valid node properties (no blank lines or text allowed).
                while j < n:
                    cand = raw_lines[j]
                    if PROPERTY_DRAWER_END.match(cand):
                        drawer_lines.append(cand)
                        found_end = True
                        j += 1
                        break
                    elif NODE_PROPERTY.match(cand):
                        drawer_lines.append(cand)
                        j += 1
                    else:
                        # Any invalid line breaks the property drawer structure.
                        all_properties = False
                        break

                # Emit a drawer only when closed with exclusively property lines.
                if found_end and all_properties:
                    result.append(PropertyDrawer.from_lines(drawer_lines))
                    i = j
                    continue

            block_begin = BLOCK_BEGIN.match(line)
            if block_begin and not block_begin.group("indent"):
                name = block_begin.group("name").lower()
                arguments = block_begin.group("args") or ""
                block_lines = [line]
                j = i + 1
                found_end = False

                while j < n:
                    block_end = BLOCK_END.match(raw_lines[j])
                    is_end = (
                        block_end is not None
                        and not block_end.group("indent")
                        and block_end.group("name").lower() == name
                    )
                    if is_end:
                        block_lines.append(raw_lines[j])
                        found_end = True
                        j += 1
                        break
                    block_lines.append(raw_lines[j])
                    j += 1

                if found_end:
                    result.append(
                        Block(name=name, arguments=arguments,
                              raw_lines=block_lines))
                    i = j
                    continue

            latex_begin = LATEX_BLOCK_BEGIN.match(line)
            if latex_begin and not latex_begin.group("indent"):
                delimiter = latex_begin.group("delimiter")
                block_type = LATEX_BLOCK_TYPE_BY_DELIMITER[delimiter]
                end_delimiter = LATEX_DELIMITERS[delimiter]
                latex_lines = [line]
                j = i + 1
                found_end = False

                while j < n:
                    latex_end = LATEX_BLOCK_END.match(raw_lines[j])
                    is_end = (
                        latex_end is not None
                        and not latex_end.group("indent")
                        and latex_end.group("delimiter") == end_delimiter
                    )
                    if is_end:
                        latex_lines.append(raw_lines[j])
                        found_end = True
                        j += 1
                        break
                    latex_lines.append(raw_lines[j])
                    j += 1

                if found_end:
                    result.append(
                        LatexBlock(type=block_type, delimiter=delimiter,
                                   text="".join(latex_lines)))
                    i = j
                    continue

            title = TITLE.match(line)
            if title:
                result.append(Title(value=title.group("value"), raw_line=line))
                i += 1
                continue

            filetags = FILETAGS.match(line)
            if filetags:
                tags = [
                    tag for tag in filetags.group("tags").split(":") if tag
                ]
                result.append(FileTags(tags=tags, raw_line=line))
                i += 1
                continue

            headline = HEADLINE.match(line)
            if headline:
                result.append(
                    Headline(level=len(headline.group("stars")),
                             title=headline.group("title"),
                             raw_line=line))
                i += 1
                continue

            list_item = LIST_ITEM.match(line)
            if (
                list_item
                and not list_item.group("indent")
                and list_item.group("bullet") != "*"
            ):
                result.append(
                    ListItem(bullet=list_item.group("bullet"),
                             value=list_item.group("value") or "",
                             raw_line=line))
                i += 1
                continue

            # Unrecognized lines or invalid structures are preserved verbatim.
            result.append(line)
            i += 1

        return result

    def __call__(self, source: LineSource) -> list[FirstPassElement]:
        # Allow parser instances to be invoked directly as callables.
        return self.parse(source)


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
    "FileTags",
    "FirstPassElement",
    "FirstPassParser",
    "Headline",
    "LatexBlock",
    "LatexBlockType",
    "LineSource",
    "ListItem",
    "NodeProperty",
    "PropertyDrawer",
    "Title",
    "parse_first_pass",
]
