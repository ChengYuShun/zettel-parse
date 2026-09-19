"""Top-level parser for custom Org-mode variant.

This module provides the top-level parsing pass that ingests an iterable
of lines or bytes and outputs a higher-level structure, including parsed
property drawers.
"""

from __future__ import annotations

from collections.abc import ItemsView, Iterable, Iterator, KeysView, ValuesView
from dataclasses import dataclass, field
from typing import Union

from zettel_parser.regex import (
    INDENTATION,
    NODE_PROPERTY,
    PROPERTY_DRAWER_BEGIN,
    PROPERTY_DRAWER_END,
)

LineSource = Union[Iterable[Union[str, bytes]], str, bytes]


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


TopLevelElement = Union[str, PropertyDrawer]


class TopLevelParser:
    """Top-level parser pass for Org-mode documents.

    Consumes an iterable of lines or raw text/bytes and produces
    the top-level document structure containing lines and parsed property drawers.
    """

    def __init__(self,
                 encoding: str = "utf-8",
                 errors: str = "strict") -> None:
        self.encoding = encoding
        self.errors = errors

    def _normalize_lines(self, source: LineSource) -> list[str]:
        if isinstance(source, (str, bytes)):
            if isinstance(source, bytes):
                source = source.decode(self.encoding, errors=self.errors)
            return source.splitlines(keepends=True)

        lines: list[str] = []
        for line in source:
            if isinstance(line, bytes):
                text = line.decode(self.encoding, errors=self.errors)
            elif isinstance(line, str):
                text = line
            else:
                raise TypeError(
                    f"Expected line to be str or bytes, got {type(line).__name__}"
                )
            if "\n" in text or "\r" in text:
                lines.extend(text.splitlines(keepends=True))
            else:
                lines.append(text)
        return lines

    def _create_property_drawer(self,
                                drawer_lines: list[str]) -> PropertyDrawer:
        first_line = drawer_lines[0]
        indent_match = INDENTATION.match(first_line)
        indent = indent_match.group(0) if indent_match else ""

        node_properties: list[NodeProperty] = []
        properties: dict[str, str] = {}

        for line in drawer_lines[1:-1]:
            m = NODE_PROPERTY.match(line)
            if m:
                name = m.group("name")
                append = m.group("append") == "+"
                val = m.group("value")
                value = "" if val is None else val

                node_properties.append(
                    NodeProperty(name=name, value=value, append=append))

                existing_key: str | None = None
                for k in properties:
                    if k.upper() == name.upper():
                        existing_key = k
                        break

                target_key = existing_key if existing_key is not None else name

                if append and existing_key is not None:
                    prev = properties[target_key]
                    if prev and value:
                        properties[target_key] = f"{prev} {value}"
                    elif value:
                        properties[target_key] = value
                else:
                    properties[target_key] = value

        return PropertyDrawer(
            properties=properties,
            node_properties=node_properties,
            raw_lines=drawer_lines,
            indent=indent,
        )

    def parse(self, source: LineSource) -> list[TopLevelElement]:
        """Parse source lines or bytes into higher-level structures."""
        raw_lines = self._normalize_lines(source)
        result: list[TopLevelElement] = []
        i = 0
        n = len(raw_lines)

        while i < n:
            line = raw_lines[i]
            if PROPERTY_DRAWER_BEGIN.match(line):
                drawer_lines = [line]
                j = i + 1
                found_end = False
                all_properties = True

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
                        all_properties = False
                        break

                if found_end and all_properties:
                    result.append(self._create_property_drawer(drawer_lines))
                    i = j
                    continue

            result.append(line)
            i += 1

        return result

    def __call__(self, source: LineSource) -> list[TopLevelElement]:
        return self.parse(source)


def parse_toplevel(
    source: LineSource,
    encoding: str = "utf-8",
    errors: str = "strict",
) -> list[TopLevelElement]:
    """Parse an iterable of lines or bytes into a top-level structure.

    Extracts property drawers while preserving other lines verbatim.
    """
    return TopLevelParser(encoding=encoding, errors=errors).parse(source)


parse = parse_toplevel

__all__ = [
    "LineSource",
    "NodeProperty",
    "PropertyDrawer",
    "TopLevelElement",
    "TopLevelParser",
    "parse",
    "parse_toplevel",
]
