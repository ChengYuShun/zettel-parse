"""Top-level parser for custom Org-mode variant.

This module provides the top-level parsing pass that ingests an iterable
of lines or bytes and outputs a higher-level structure, including parsed
property drawers, blocks, LaTeX expressions, and special lines (titles,
headlines, and list items).
"""

from __future__ import annotations

from collections.abc import ItemsView, Iterable, Iterator, KeysView, ValuesView
from dataclasses import dataclass, field
from enum import Enum

from zettel_parser.common_regex import (
    BLOCK_BEGIN,
    BLOCK_END,
    HEADLINE,
    INDENTATION,
    LATEX_BLOCK_BEGIN,
    LATEX_BLOCK_END,
    LATEX_DELIMITERS,
    LIST_ITEM,
    NODE_PROPERTY,
    PROPERTY_DRAWER_BEGIN,
    PROPERTY_DRAWER_END,
    TITLE,
)

LineSource = Iterable[str | bytes] | str | bytes


@dataclass(frozen=True)
class NodeProperty:
    """A single node property definition within a property drawer.

    Attributes:
        name: The property name (without enclosing colons).
        value: The property value string.
        append: True if defined with '+' append syntax (':NAME+:').
    """

    name: str
    value: str = ""
    append: bool = False


@dataclass
class PropertyDrawer:
    """An Org-mode property drawer (:PROPERTIES: ... :END:).

    Attributes:
        properties: Mapping of property names to accumulated values.
            Properties defined with '+' append syntax are concatenated with
            a space separator.
        node_properties: Ordered list of individual NodeProperty entries.
        raw_lines: Verbatim source lines comprising this drawer.
        indent: Indentation of the opening :PROPERTIES: line.
    """

    properties: dict[str, str] = field(default_factory=dict)
    node_properties: list[NodeProperty] = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list, compare=False)
    indent: str = field(default="", compare=False)

    def __post_init__(self) -> None:
        if self.properties and not self.node_properties:
            self.node_properties = [
                NodeProperty(name=k, value=v)
                for k, v in self.properties.items()
            ]

    @classmethod
    def from_lines(cls, lines: list[str]) -> PropertyDrawer:
        """Create a property drawer from its verbatim source lines.

        The first and last lines are treated as the opening and closing
        delimiters; every line in between is parsed as a node property.

        Args:
            lines: The source lines comprising the drawer.

        Returns:
            A new PropertyDrawer instance.
        """
        indent_match = INDENTATION.match(lines[0])
        indent = indent_match.group(0) if indent_match else ""

        node_properties: list[NodeProperty] = []
        properties: dict[str, str] = {}

        for line in lines[1:-1]:
            match = NODE_PROPERTY.match(line)
            if match is None:
                continue

            name = match.group("name")
            append = match.group("append") == "+"
            raw_value = match.group("value")
            value = "" if raw_value is None else raw_value

            node_properties.append(
                NodeProperty(name=name, value=value, append=append))

            existing_key: str | None = None
            for key in properties:
                if key.upper() == name.upper():
                    existing_key = key
                    break

            target_key = existing_key if existing_key is not None else name

            if append and existing_key is not None:
                previous = properties[target_key]
                if previous and value:
                    properties[target_key] = f"{previous} {value}"
                elif value:
                    properties[target_key] = value
            else:
                properties[target_key] = value

        return cls(
            properties=properties,
            node_properties=node_properties,
            raw_lines=lines,
            indent=indent,
        )

    def __getitem__(self, key: str) -> str:
        """Retrieve a property value case-insensitively.

        Raises KeyError if the property does not exist.
        """
        if key in self.properties:
            return self.properties[key]
        key_upper = key.upper()
        for k, v in self.properties.items():
            if k.upper() == key_upper:
                return v
        raise KeyError(key)

    def get(self, key: str, default: str | None = None) -> str | None:
        """Retrieve a property value case-insensitively with fallback."""
        try:
            return self[key]
        except KeyError:
            return default

    def get_all(self, key: str) -> list[str]:
        """Return all defined values for a property name in order (case-insensitive)."""
        key_upper = key.upper()
        return [
            prop.value for prop in self.node_properties
            if prop.name.upper() == key_upper
        ]

    def __contains__(self, key: object) -> bool:
        """Check if a property exists case-insensitively."""
        if not isinstance(key, str):
            return False
        if key in self.properties:
            return True
        key_upper = key.upper()
        return any(k.upper() == key_upper for k in self.properties)

    def __iter__(self) -> Iterator[str]:
        """Iterate over property keys."""
        return iter(self.properties)

    def __len__(self) -> int:
        """Return the number of unique properties."""
        return len(self.properties)

    def items(self) -> ItemsView[str, str]:
        """Return a view of property (key, value) pairs."""
        return self.properties.items()

    def keys(self) -> KeysView[str]:
        """Return a view of property keys."""
        return self.properties.keys()

    def values(self) -> ValuesView[str]:
        """Return a view of property values."""
        return self.properties.values()

    def __str__(self) -> str:
        """Return the verbatim representation of the property drawer."""
        return "".join(self.raw_lines)


@dataclass
class Block:
    """An Org-mode block (#+begin_NAME ... #+end_NAME).

    Attributes:
        name: The block name, normalized to lower case (e.g. ``src``).
        arguments: The text following the block name on the begin line.
        raw_lines: Verbatim source lines comprising this block.
    """

    name: str
    arguments: str = ""
    raw_lines: list[str] = field(default_factory=list, compare=False)

    @property
    def body(self) -> str:
        """Return the text between the begin and end lines."""
        return "".join(self.raw_lines[1:-1])

    @property
    def body_lines(self) -> list[str]:
        """Return the lines between the begin and end lines."""
        return list(self.raw_lines[1:-1])

    def __str__(self) -> str:
        """Return the verbatim representation of the block."""
        return "".join(self.raw_lines)


class LatexBlockType(Enum):
    """The recognized flavors of block-level LaTeX expression."""

    BRACKET = "bracket"
    EQUATION = "equation"
    TIKZCD = "tikzcd"


LATEX_BLOCK_TYPE_BY_DELIMITER: dict[str, LatexBlockType] = {
    r"\[": LatexBlockType.BRACKET,
    r"\begin{equation*}": LatexBlockType.EQUATION,
    r"\begin{tikzcd}": LatexBlockType.TIKZCD,
}


@dataclass
class LatexBlock:
    """A block-level LaTeX expression.

    Attributes:
        type: The flavor of the expression.
        delimiter: The opening delimiter, one of ``LATEX_DELIMITERS`` keys
            (e.g. ``\\[`` or ``\\begin{tikzcd}``).
        text: The complete verbatim expression, including both delimiters and
            every newline in between.
    """

    type: LatexBlockType
    delimiter: str
    text: str

    @property
    def end_delimiter(self) -> str:
        """Return the closing delimiter paired with this opening delimiter."""
        return LATEX_DELIMITERS[self.delimiter]

    def __str__(self) -> str:
        """Return the complete verbatim expression."""
        return self.text


@dataclass
class Title:
    """A document title keyword (#+title: ...).

    Attributes:
        value: The title text following the keyword.
        raw_line: Verbatim source line comprising this title.
    """

    value: str
    raw_line: str = field(default="", compare=False)

    def __str__(self) -> str:
        """Return the verbatim representation of the title line."""
        return self.raw_line


@dataclass
class Headline:
    """An Org-mode headline (one or more leading stars and a title).

    Attributes:
        level: The outline level, i.e. the number of leading stars.
        title: The headline text after the stars.
        raw_line: Verbatim source line comprising this headline.
    """

    level: int
    title: str
    raw_line: str = field(default="", compare=False)

    def __str__(self) -> str:
        """Return the verbatim representation of the headline."""
        return self.raw_line


@dataclass
class ListItem:
    """A plain list item line, ordered or unordered.

    Attributes:
        bullet: The list marker (e.g. ``-``, ``+``, ``1.``, ``a)``).
        value: The item text following the marker.
        raw_line: Verbatim source line comprising this list item.
    """

    bullet: str
    value: str
    raw_line: str = field(default="", compare=False)

    @property
    def ordered(self) -> bool:
        """Return True if this is an ordered list item."""
        return self.bullet not in ("-", "+")

    def __str__(self) -> str:
        """Return the verbatim representation of the list item."""
        return self.raw_line


TopLevelElement = (
    str | PropertyDrawer | Block | LatexBlock | Title | Headline | ListItem
)


class TopLevelParser:
    """Top-level parser pass for Org-mode documents.

    Consumes an iterable of lines or raw text/bytes and produces
    the top-level document structure containing lines, property drawers,
    blocks, LaTeX expressions, and special lines.
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

    def parse(self, source: LineSource) -> list[TopLevelElement]:
        """Parse source lines or bytes into higher-level structures."""
        raw_lines = self._normalize_lines(source)
        result: list[TopLevelElement] = []
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
            if block_begin:
                name = block_begin.group("name").lower()
                arguments = block_begin.group("args") or ""
                block_lines = [line]
                j = i + 1
                found_end = False

                while j < n:
                    block_end = BLOCK_END.match(raw_lines[j])
                    if block_end and block_end.group("name").lower() == name:
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
            if latex_begin:
                delimiter = latex_begin.group("delimiter")
                block_type = LATEX_BLOCK_TYPE_BY_DELIMITER[delimiter]
                end_delimiter = LATEX_DELIMITERS[delimiter]
                latex_lines = [line]
                j = i + 1
                found_end = False

                while j < n:
                    latex_end = LATEX_BLOCK_END.match(raw_lines[j])
                    if latex_end and latex_end.group("delimiter") == end_delimiter:
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

            headline = HEADLINE.match(line)
            if headline:
                result.append(
                    Headline(level=len(headline.group("stars")),
                             title=headline.group("title"),
                             raw_line=line))
                i += 1
                continue

            list_item = LIST_ITEM.match(line)
            if list_item:
                result.append(
                    ListItem(bullet=list_item.group("bullet"),
                             value=list_item.group("value"),
                             raw_line=line))
                i += 1
                continue

            # Unrecognized lines or invalid structures are preserved verbatim.
            result.append(line)
            i += 1

        return result

    def __call__(self, source: LineSource) -> list[TopLevelElement]:
        # Allow parser instances to be invoked directly as callables.
        return self.parse(source)


def parse_toplevel(
    source: LineSource,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> list[TopLevelElement]:
    """Parse an iterable of lines or bytes into a top-level structure.

    Extracts property drawers, blocks, and LaTeX expressions while preserving
    other lines verbatim.
    """
    return TopLevelParser(encoding=encoding, errors=errors).parse(source)


parse = parse_toplevel

__all__ = [
    "Block",
    "Headline",
    "LatexBlock",
    "LatexBlockType",
    "LineSource",
    "ListItem",
    "NodeProperty",
    "PropertyDrawer",
    "Title",
    "TopLevelElement",
    "TopLevelParser",
    "parse",
    "parse_toplevel",
]
