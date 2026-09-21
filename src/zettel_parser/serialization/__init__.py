"""Serialization of the parsed AST into several output formats.

The AST is first converted to a canonical, JSON-compatible representation by
:func:`~zettel_parser.serialization.ir.to_data`, and each format renderer then
renders that representation.  :func:`serialize` dispatches on a format name
through the :data:`SERIALIZERS` registry, which callers may extend with
:func:`register_serializer`.
"""

from __future__ import annotations

from collections.abc import Callable

from zettel_parser.serialization.ir import Data, to_data
from zettel_parser.serialization.json_renderer import to_json
from zettel_parser.serialization.org_renderer import to_org
from zettel_parser.serialization.text_renderer import to_text
from zettel_parser.serialization.xml_renderer import to_xml

Renderer = Callable[[object], str]

SERIALIZERS: dict[str, Renderer] = {
    "json": to_json,
    "xml": to_xml,
    "text": to_text,
    "org": to_org,
}


def register_serializer(name: str, renderer: Renderer) -> None:
    """Register or replace a renderer under ``name``.

    Args:
        name: The format name used with :func:`serialize`.
        renderer: A callable mapping an AST node to text.
    """
    SERIALIZERS[name] = renderer


def serialize(node: object, fmt: str = "json") -> str:
    """Serialize an AST node into the requested format.

    Args:
        node: The AST node to serialize.
        fmt: One of the keys of :data:`SERIALIZERS` (``"json"``, ``"xml"``,
            ``"text"``, or ``"org"``).

    Returns:
        The serialized text.

    Raises:
        ValueError: If ``fmt`` is not a registered format.
    """
    try:
        renderer = SERIALIZERS[fmt]
    except KeyError:
        choices = ", ".join(sorted(SERIALIZERS))
        raise ValueError(
            f"Unknown format {fmt!r}; choose one of: {choices}"
        ) from None
    return renderer(node)


__all__ = [
    "Data",
    "Renderer",
    "SERIALIZERS",
    "register_serializer",
    "serialize",
    "to_data",
    "to_json",
    "to_org",
    "to_text",
    "to_xml",
]
