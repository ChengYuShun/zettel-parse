"""Property drawer elements produced by the first parsing pass."""

from __future__ import annotations

from collections.abc import ItemsView, Iterator, KeysView, ValuesView
from dataclasses import dataclass, field

from zettel_parser.common_regex import INDENTATION, NODE_PROPERTY


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
