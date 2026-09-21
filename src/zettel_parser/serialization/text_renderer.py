"""Text renderer for the structure-pass AST.

This produces the compact, deterministic outline used by the snapshot tests:
only node types and salient scalar values are emitted, so the result is stable
across edits to raw text, whitespace, and line endings.
"""

from __future__ import annotations

from collections.abc import Iterable

from zettel_parser.first_pass_elements import Block, LatexBlock, PropertyDrawer
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

_INDENT = "  "


def _emit(lines: list[str], depth: int, text: str) -> None:
    lines.append(_INDENT * depth + text)


def _describe_all(nodes: Iterable[object], depth: int, lines: list[str]) -> None:
    for node in nodes:
        _describe(node, depth, lines)


def _describe_optional(
    node: object | None, depth: int, lines: list[str]
) -> None:
    if node is not None:
        _describe(node, depth, lines)


def _describe_properties(
    drawer: PropertyDrawer | None, depth: int, lines: list[str]
) -> None:
    if drawer is None:
        return
    pairs = ", ".join(f"{key}={value!r}" for key, value in drawer.items())
    _emit(lines, depth, f"Properties {pairs}")


def _describe(node: object, depth: int, lines: list[str]) -> None:
    match node:
        case Zettel():
            _emit(
                lines,
                depth,
                f"Zettel title={node.title!r} filetags={node.filetags!r}",
            )
            _describe_properties(node.properties, depth + 1, lines)
            _describe_optional(node.body, depth + 1, lines)
            _describe_all(node.children, depth + 1, lines)
        case Headline():
            _emit(
                lines,
                depth,
                f"Headline level={node.level} title={node.title!r}",
            )
            _describe_properties(node.properties, depth + 1, lines)
            _describe_optional(node.body, depth + 1, lines)
            _describe_all(node.children, depth + 1, lines)
        case FlatText():
            _emit(lines, depth, "FlatText")
            _describe_all(node.elements, depth + 1, lines)
        case Paragraph():
            _emit(lines, depth, "Paragraph")
            _describe_all(node.elements, depth + 1, lines)
        case ParagraphText():
            _emit(lines, depth, "ParagraphText")
            _describe_all(node.elements, depth + 1, lines)
        case List():
            _emit(lines, depth, f"List bullet={node.bullet_type!r}")
            _describe_all(node.elements, depth + 1, lines)
        case ListItem():
            checked = "None" if node.checked is None else node.checked.name
            _emit(lines, depth, f"Item value={node.value!r} checked={checked}")
            _describe_optional(node.body, depth + 1, lines)
        case BlankLines():
            _emit(lines, depth, f"BlankLines x{len(node.raw_lines)}")
        case Block():
            _emit(
                lines,
                depth,
                f"Block name={node.name!r} arguments={node.arguments!r}",
            )
        case LatexBlock():
            _emit(
                lines,
                depth,
                f"LatexBlock type={node.type.name}, text={node.text!r}",
            )
        case InlineLatex():
            _emit(lines, depth, f"InlineLatex content={node.content!r}")
        case Link():
            _emit(lines, depth, f"Link target={node.target!r}")
            if node.description is not None:
                _describe_all(node.description, depth + 1, lines)
        case Verbatim():
            _emit(lines, depth, f"Verbatim text={node.text!r}")
        case Code():
            _emit(lines, depth, f"Code text={node.text!r}")
        case Bold() | Italic() | Underline() | StrikeThrough():
            _emit(lines, depth, type(node).__name__)
            _describe_all(node.elements, depth + 1, lines)
        case str():
            _emit(lines, depth, f"str {node!r}")
        case _:
            _emit(lines, depth, type(node).__name__)


def to_text(node: object) -> str:
    """Render an AST node as a compact, deterministic text outline.

    Args:
        node: The AST node to render.

    Returns:
        The outline, ending in a newline.
    """
    lines: list[str] = []
    _describe(node, 0, lines)
    return "\n".join(lines) + "\n"


__all__ = ["to_text"]
