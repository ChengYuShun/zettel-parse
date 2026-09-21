"""Canonical intermediate representation shared by every serializer.

The AST is walked exactly once into a tree of JSON-compatible values.  Format
renderers (:mod:`zettel_parser.serialization.json_renderer`,
:mod:`zettel_parser.serialization.xml_renderer`,
:mod:`zettel_parser.serialization.text_renderer`, and
:mod:`zettel_parser.serialization.org_renderer`) then only have to deal with
that tree, so the type dispatch lives in one place.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TypeAlias

from zettel_parser.first_pass_elements import (
    Block,
    LatexBlock,
    NodeProperty,
    PropertyDrawer,
)
from zettel_parser.inline_pass import (
    Bold,
    Code,
    InlineLatex,
    Italic,
    Link,
    StrikeThrough,
    Underline,
    Verbatim,
)
from zettel_parser.structure_pass_elements import (
    BlankLines,
    FlatText,
    Headline,
    List,
    ListItem,
    Paragraph,
    ParagraphText,
    Zettel,
)

# A JSON-compatible value.  Plain text is a bare string; every AST object is a
# mapping tagged with ``"type": <class name>``.
#
# At the moment, the type ``dict`` is always used to represent an AST node, and
# never its data, so it is guaranteed to have the key ``"type"`` in it.  The
# type ``list`` is used to either represent a list of child elements or a list
# of mixed content, or a list of a specific data type, e.g. a list of
# ``NodeProperty``'s.
Data: TypeAlias = (
    None | bool | int | float | str | list["Data"] | dict[str, "Data"]
)


def _tag(type_name: str, **fields: Data) -> dict[str, Data]:
    """Build a tagged mapping, keeping ``"type"`` as the first key."""
    return {"type": type_name, **fields}


def to_data(node: object) -> Data:
    """Convert a structure-pass AST node into its canonical representation.

    Only the structure-pass AST (and the first-pass elements embedded in it)
    is supported: later occurrences collapse information, and the first-pass
    ``Headline``/``ListItem``/``FileTags``/``Title`` objects do not appear in
    a :class:`~zettel_parser.structure_pass_elements.Zettel`.

    Args:
        node: An AST node, a ``None``, or (inside a collection field) a plain
            string.  Plain strings are returned unchanged.

    Returns:
        A JSON-compatible value: ``None``, a scalar, a bare string, a list, or
        a mapping tagged with its originating class name.

    Raises:
        TypeError: If ``node`` is not part of the supported AST.
    """
    match node:
        case None:
            return None
        case str():
            return node
        case Zettel():
            return _tag(
                "Zettel",
                title=node.title,
                level=node.level,
                filetags=node.filetags,
                properties=to_data(node.properties),
                body=to_data(node.body),
                children=list(map(to_data, node.children))
            )
        case Headline():
            return _tag(
                "Headline",
                title=node.title,
                level=node.level,
                properties=to_data(node.properties),
                body=to_data(node.body),
                children=list(map(to_data, node.children)),
            )
        case PropertyDrawer():
            return _tag(
                "PropertyDrawer",
                properties=dict(node.properties),
                node_properties=list(map(to_data, node.node_properties)),
            )
        case NodeProperty():
            return _tag(
                "NodeProperty",
                name=node.name,
                value=node.value,
                append=node.append,
            )
        case Block():
            return _tag(
                "Block",
                name=node.name,
                arguments=node.arguments,
                body=node.body,
            )
        case LatexBlock():
            return _tag(
                "LatexBlock",
                latex_type=node.type.value,
                delimiter=node.delimiter,
                text=node.text,
            )
        case FlatText():
            return _tag("FlatText", elements=_elements(node.elements))
        case Paragraph():
            return _tag("Paragraph", elements=_elements(node.elements))
        case ParagraphText():
            return _tag(
                "ParagraphText",
                text=node.text,
                elements=_elements(node.elements),
            )
        case List():
            return _tag(
                "List",
                bullet_type=node.bullet_type,
                elements=_elements(node.elements),
            )
        case ListItem():
            checked = None if node.checked is None else node.checked.value
            return _tag(
                "ListItem",
                bullet=node.bullet,
                checked=checked,
                lines=list(node.lines),
                body=to_data(node.body),
            )
        case BlankLines():
            return _tag("BlankLines", text=node.text)
        case InlineLatex():
            return _tag("InlineLatex", content=node.content)
        case Link():
            description = (
                None
                if node.description is None
                else _elements(node.description)
            )
            return _tag(
                "Link", target=node.target, description=description
            )
        case Verbatim():
            return _tag("Verbatim", text=node.text)
        case Code():
            return _tag("Code", text=node.text)
        case Bold():
            return _tag("Bold", elements=_elements(node.elements))
        case Italic():
            return _tag("Italic", elements=_elements(node.elements))
        case Underline():
            return _tag("Underline", elements=_elements(node.elements))
        case StrikeThrough():
            return _tag("StrikeThrough", elements=_elements(node.elements))
        case _:
            raise TypeError(
                f"Cannot serialize object of type {type(node).__name__}"
            )


def _elements(elements: Sequence[object]) -> list[Data]:
    """Convert a heterogeneous sequence of AST parts into ``Data`` values."""
    return list(map(to_data, elements))


__all__ = ["Data", "to_data"]
