"""XML renderer for the canonical AST representation.

Every AST object becomes an element named after its class in kebab-case
(``ParagraphText`` -> ``paragraph-text``).  Its fields are mapped as follows:

* scalars become attributes (``None`` is omitted);
* every list is rendered as mixed content, i.e. its nodes become child elements
  and its strings become text;
* a mixed type is emitted on one line, while an element-only type is indented
  on separate lines.

Two terms recur below:

* **scalar** -- a boolean, a number, or a string.  ``None`` is not a scalar;
  such fields are omitted.
* **mixed content** -- text interleaved with child elements, as in
  ``Hello <italic>world</italic>!``.  Indentation whitespace would change the
  text, so mixed elements are emitted on a single line.
"""

from __future__ import annotations

from xml.sax.saxutils import escape, quoteattr

from zettel_parser.serialization.ir import Data, to_data

# Fields omitted from the XML because a sibling already carries them:
# ParagraphText.text repeats its elements, PropertyDrawer.properties is the
# merged view of node_properties, and ListItem.lines repeats its body.
_SKIP_FIELDS: dict[str, frozenset[str]] = {
    "ParagraphText": frozenset({"text"}),
    "PropertyDrawer": frozenset({"properties"}),
    "ListItem": frozenset({"lines"}),
}

# Node types whose content is mixed.  Only these keep text and markup on one
# line; only these may hold bare strings among their markup.
_MIXED_TYPES: frozenset[str] = frozenset(
    {
        "ParagraphText",
        "Bold",
        "Italic",
        "Underline",
        "StrikeThrough",
        "Link",
    }
)

# The indentation unit for element-only children.
_INDENT = "  "


def _kebab(name: str) -> str:
    """Convert an identifier to kebab-case.

    ``InlineLatex`` -> ``inline-latex``; ``bullet_type`` -> ``bullet-type``.
    """
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


def _is_node(value: Data) -> bool:
    """Return True if ``value`` is a tagged node (a mapping with ``type``)."""
    return isinstance(value, dict) and "type" in value


def _is_scalar(value: Data) -> bool:
    """Return True if ``value`` is a non-``None`` scalar."""
    return not isinstance(value, (dict, list)) and value is not None


def _scalar_to_str(value: Data) -> str:
    """Return a scalar as text; booleans become ``"true"``/``"false"``."""
    assert _is_scalar(value)
    if isinstance(value, bool):
        return "true" if value is True else "false"
    return str(value)


def _render_mixed_content(items: list[Data], depth: int) -> list[str]:
    """Render one collection field and return its fragments in order.

    Args:
        items: The field's values, in order.
        depth: Current indentation depth.

    Example::

        _render_mixed_content(["a ", {"type": "Italic", "elements": ["b"]}],
                              0)
            ->  ["a ", "<italic>b</italic>"]
    """
    ret: list[str] = []
    for item in items:
        if item is None:
            continue
        if _is_node(item):
            assert isinstance(item, dict)
            ret.append(_render(item, depth + 1))
        else:
            ret.append(escape(_scalar_to_str(item)))
    return ret


def _assemble_element(
    tag: str,
    attrs: dict[str, str],
    content_or_children: list[str],
    depth: int,
    use_mixed_content: bool,
) -> str:
    """Assemble a node's collected fragments into one XML element.

    Args:
        tag: The element name, already kebab-cased.
        attrs: The attributes as a ``dict``; keys are in snake case and values
            are not escaped yet (this function escapes them).
        content_or_children: The rendered fragments, in order.  Its meaning
            depends on ``use_mixed_content``: mixed content (text fragments and
            inline elements) when that is True, child elements to indent when
            it is False.
        depth: Current indentation depth.
        use_mixed_content: Whether the node is a mixed type.  Mixed nodes are
            emitted on a single line; the rest are indented.

    Example::

        _assemble_element("italic", {}, ["<bold>hi</bold>"], 0, True)
            ->  <italic><bold>hi</bold></italic>

        _assemble_element("flat-text", {}, ["<paragraph>...</paragraph>"],
                          0, False)
            ->  <flat-text>
                  <paragraph>...</paragraph>
                </flat-text>
    """
    attr_text = "".join(
        f" {_kebab(key)}={quoteattr(value)}" for key, value in attrs.items()
    )
    if not content_or_children:
        return f"<{tag}{attr_text}/>"
    if use_mixed_content:
        # Text and markup are joined without any added whitespace.
        inner = "".join(content_or_children)
        return f"<{tag}{attr_text}>{inner}</{tag}>"
    else:
        pad = _INDENT * (depth + 1)
        body = "".join(f"{pad}{child}\n" for child in content_or_children)
        return f"<{tag}{attr_text}>\n{body}{_INDENT * depth}</{tag}>"


def _render(node: dict[str, Data], depth: int) -> str:
    """Render one tagged node as an XML element.

    Args:
        node: A tagged node produced by :func:`to_data`.
        depth: Current indentation depth.

    Example::

        ParagraphText ->
            <paragraph-text>a <italic>b</italic></paragraph-text>

        FlatText with element children ->
            <flat-text>
              <paragraph>...</paragraph>
            </flat-text>
    """
    element_type = node["type"]
    assert isinstance(element_type, str)
    tag = _kebab(element_type)
    # Which fields to skip.
    skip_fields = _SKIP_FIELDS.get(element_type, frozenset())
    # Whether to render inline content interleaved with text.
    use_mixed_content = element_type in _MIXED_TYPES

    # This variable collects all scalar values.
    attrs: dict[str, str] = {}
    # This variable collects the rendered version of all fields of type list,
    # in the field's order.  Lists are rendered as mixed content, so their
    # nodes become child elements and their strings become text.
    content_or_children: list[str] = []

    for key, value in node.items():
        if key == "type" or key in skip_fields or value is None:
            continue
        if _is_scalar(value):
            attrs[key] = _scalar_to_str(value)
        elif isinstance(value, dict):
            content_or_children.append(_render(value, depth + 1))
        elif isinstance(value, list):
            content_or_children += _render_mixed_content(value, depth)
        else:
            raise TypeError(
                f"Cannot render value of type {type(value).__name__}"
            )

    return _assemble_element(
        tag, attrs, content_or_children, depth, use_mixed_content
    )


def to_xml(node: object) -> str:
    """Render an AST node as an XML document.

    Args:
        node: Any structure-pass AST node.

    Returns:
        XML text: an XML declaration, the root element, and a trailing newline.
    """
    data = to_data(node)
    if not isinstance(data, dict):
        raise TypeError("to_xml expects a single AST node")
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n' + _render(data, 0) + "\n"
    )


__all__ = ["to_xml"]
