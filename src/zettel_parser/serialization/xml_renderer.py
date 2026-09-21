"""XML renderer for the canonical AST representation.

The rendering rules are deliberately generic:

* every AST object becomes an element named after its class in kebab-case;
* scalar fields become attributes, except multi-line strings, which become
  text content;
* collections of plain scalars become repeated child elements (``filetags``
  giving ``<filetag>``, ``lines`` giving ``<line>``);
* inline collections (``elements`` and a link ``description``) become mixed
  content, with bare strings as text nodes and markup as child elements;
* a node whose content is mixed (or contains a text run) is emitted compactly,
  while element-only nodes are indented.
"""

from __future__ import annotations

from xml.sax.saxutils import escape, quoteattr

from zettel_parser.serialization.ir import Data, to_data

# Fields that are already represented elsewhere in the XML output.
_SKIP_FIELDS: dict[str, frozenset[str]] = {
    "ParagraphText": frozenset({"text"}),
    "PropertyDrawer": frozenset({"properties"}),
    "ListItem": frozenset({"lines"}),
}

# Collection fields that hold inline content rather than a collection of
# scalar children.
_CONTENT_KEYS: frozenset[str] = frozenset({"elements", "description"})

_INDENT = "  "


def _kebab(name: str) -> str:
    """Convert a CamelCase or snake_case identifier to kebab-case."""
    parts: list[str] = []
    for index, char in enumerate(name):
        if char == "_":
            parts.append("-")
        elif char.isupper():
            if index > 0:
                parts.append("-")
            parts.append(char.lower())
        else:
            parts.append(char)
    return "".join(parts)


def _singular(key: str) -> str:
    """Return a repeated-element name for a scalar collection field."""
    if key.endswith("s") and not key.endswith("ss"):
        return key[:-1]
    return key


def _is_node(value: Data) -> bool:
    """Return whether a value is a tagged AST node mapping."""
    return isinstance(value, dict) and "type" in value


def _scalar_text(value: Data) -> str:
    """Return the text form of a non-null scalar value."""
    if isinstance(value, str):
        return value
    return str(value)


def _will_be_mixed(node: dict[str, Data]) -> bool:
    """Return whether a node will produce mixed or textual content."""
    name = node.get("type")
    skip = _SKIP_FIELDS.get(name, frozenset()) if isinstance(name, str) else frozenset()
    for key, value in node.items():
        if key == "type" or key in skip or value is None:
            continue
        if isinstance(value, str) and "\n" in value:
            return True
        if (
            isinstance(value, list)
            and key in _CONTENT_KEYS
            and any(
                item is not None and not _is_node(item) for item in value
            )
        ):
            return True
    return False


def _render_plain_mapping(
    key: str, mapping: dict[str, Data], depth: int
) -> str:
    """Render an untagged mapping (e.g. a drawer's merged properties)."""
    element = _kebab(key)
    entries = [
        f"<entry name={quoteattr(name)} "
        f"value={quoteattr(_scalar_text(value))}/>"
        for name, value in mapping.items()
    ]
    if not entries:
        return f"<{element}/>"
    pad = _INDENT * (depth + 1)
    body = "".join(f"{pad}{entry}\n" for entry in entries)
    return f"<{element}>\n{body}{_INDENT * depth}</{element}>"


def _render_list(
    items: list[Data],
    key: str,
    depth: int,
    content: list[str],
    children: list[str],
    compact: bool,
) -> None:
    """Render a collection field, mutating ``content`` and ``children``."""
    if key in _CONTENT_KEYS:
        mixed = any(
            item is not None and not _is_node(item) for item in items
        )
        for item in items:
            if item is None:
                continue
            if _is_node(item):
                assert isinstance(item, dict)
                target = content if mixed else children
                target.append(_render(item, depth + 1, compact or mixed))
            else:
                content.append(escape(_scalar_text(item)))
        return

    item_element = _kebab(_singular(key))
    for item in items:
        if item is None:
            continue
        if _is_node(item):
            assert isinstance(item, dict)
            children.append(_render(item, depth + 1, compact))
        else:
            text = escape(_scalar_text(item))
            children.append(f"<{item_element}>{text}</{item_element}>")


def _render(node: dict[str, Data], depth: int, compact: bool) -> str:
    """Render one tagged node as an XML element."""
    name = node["type"]
    assert isinstance(name, str)
    element = _kebab(name)
    skip = _SKIP_FIELDS.get(name, frozenset())
    mixed = _will_be_mixed(node)

    attrs: dict[str, str] = {}
    content: list[str] = []
    children: list[str] = []

    for key, value in node.items():
        if key == "type" or key in skip or value is None:
            continue
        if isinstance(value, bool):
            attrs[key] = "true" if value else "false"
        elif isinstance(value, (int, float)):
            attrs[key] = str(value)
        elif isinstance(value, str):
            if "\n" in value:
                content.append(escape(value))
            else:
                attrs[key] = value
        elif isinstance(value, dict):
            if _is_node(value):
                children.append(_render(value, depth + 1, mixed))
            else:
                children.append(
                    _render_plain_mapping(key, value, depth + 1)
                )
        elif isinstance(value, list):
            _render_list(value, key, depth, content, children, mixed)
        else:
            raise TypeError(
                f"Cannot render value of type {type(value).__name__}"
            )

    attr_text = "".join(
        f" {_kebab(key)}={quoteattr(value)}" for key, value in attrs.items()
    )

    if not content and not children:
        return f"<{element}{attr_text}/>"
    if content:
        inner = "".join(content) + "".join(children)
        return f"<{element}{attr_text}>{inner}</{element}>"
    if compact:
        inner = "".join(children)
        return f"<{element}{attr_text}>{inner}</{element}>"

    pad = _INDENT * (depth + 1)
    body = "".join(f"{pad}{child}\n" for child in children)
    return f"<{element}{attr_text}>\n{body}{_INDENT * depth}</{element}>"


def to_xml(node: object) -> str:
    """Render an AST node as an XML document.

    Args:
        node: The AST node to render.

    Returns:
        The XML text, beginning with an XML declaration and ending in a
        newline.
    """
    data = to_data(node)
    if not isinstance(data, dict):
        raise TypeError("to_xml expects a single AST node")
    declaration = '<?xml version="1.0" encoding="utf-8"?>\n'
    return f"{declaration}{_render(data, 0, False)}\n"


__all__ = ["to_xml"]
