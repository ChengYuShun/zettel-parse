"""Property drawer elements produced by the first parsing pass."""

from __future__ import annotations

from dataclasses import dataclass, field

from zettel_parser.common_regex import (
    DRAWER_BEGIN,
    DRAWER_END,
    INDENTATION,
    NODE_PROPERTY,
)
from zettel_parser.cursor import Cursor


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
        node_properties: The individually parsed property lines, in order.
        raw_lines: Verbatim source lines comprising this drawer.
        indent: Indentation of the opening :PROPERTIES: line.
    """

    node_properties: list[NodeProperty] = field(default_factory=list)
    raw_lines: list[str] = field(default_factory=list, compare=False)
    indent: str = field(default="", compare=False)

    @classmethod
    def try_parse(cls, cursor: Cursor[str]) -> PropertyDrawer | None:
        """Consume a leading property drawer from ``cursor``.

        A drawer runs from a ``:PROPERTIES:`` line to its ``:END:`` line and
        may only contain node property lines in between.  If the drawer is not
        properly closed, or contains any other line, the cursor is left
        untouched and None is returned.

        Args:
            cursor: The cursor to consume lines from.

        Returns:
            A PropertyDrawer instance, or None if no drawer starts here.
        """
        begin = cursor.peek()
        if not isinstance(begin, str):
            return None
        match = DRAWER_BEGIN.match(begin)
        if match is None or match.group("name").lower() != "properties":
            return None

        indent_match = INDENTATION.match(begin)
        indent = indent_match.group(0) if indent_match else ""

        node_properties: list[NodeProperty] = []
        lines = [begin]

        offset = 1
        while (candidate := cursor.peek(offset)) is not None:
            if not isinstance(candidate, str):
                return None
            if DRAWER_END.match(candidate):
                lines.append(candidate)
                cursor.advance(offset + 1)
                return cls(
                    node_properties=node_properties,
                    raw_lines=lines,
                    indent=indent,
                )
            property_match = NODE_PROPERTY.match(candidate)
            if property_match is None:
                return None
            node_properties.append(
                NodeProperty(
                    name=property_match.group("name"),
                    value=property_match.group("value") or "",
                    append=property_match.group("append") == "+",
                )
            )
            lines.append(candidate)
            offset += 1

        return None

    @property
    def properties(self) -> dict[str, str]:
        """Return the property values, keyed by name as first written.

        Names that differ only in case refer to the same property.  A later
        occurrence overwrites the value, unless it uses the '+' append syntax,
        in which case its value is joined to the existing one by a space.
        """
        merged: dict[str, str] = {}
        for prop in self.node_properties:
            key = next(
                (name for name in merged if name.upper() == prop.name.upper()),
                prop.name,
            )
            if prop.append and key in merged:
                merged[key] = " ".join(
                    part for part in (merged[key], prop.value) if part
                )
            else:
                merged[key] = prop.value
        return merged

    def __getitem__(self, name: str) -> str:
        """Return the property named ``name``, ignoring case.

        Raises:
            KeyError: If no property has that name.
        """
        upper = name.upper()
        for key, value in self.properties.items():
            if key.upper() == upper:
                return value
        raise KeyError(name)

    def get(self, name: str, default: str | None = None) -> str | None:
        """Return the property named ``name``, or ``default`` if absent."""
        try:
            return self[name]
        except KeyError:
            return default

    def get_all(self, name: str) -> list[str]:
        """Return every value written for ``name``, in order and ignoring case."""
        upper = name.upper()
        return [
            prop.value
            for prop in self.node_properties
            if prop.name.upper() == upper
        ]

    def __str__(self) -> str:
        """Return the verbatim representation of the property drawer."""
        return "".join(self.raw_lines)


__all__ = ["NodeProperty", "PropertyDrawer"]
