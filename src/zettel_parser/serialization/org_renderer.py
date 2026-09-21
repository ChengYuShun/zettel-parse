"""Org-mode renderer for the structure-pass AST.

The output is a best-effort reconstruction and is not guaranteed to be an
exact round-trip: where an element still carries its verbatim source lines
(blocks, LaTeX blocks, property drawers, list items, blank lines) those are
echoed as-is, while headlines, the document preamble, and hand-built elements
are rebuilt from their parsed fields.
"""

from __future__ import annotations

from zettel_parser.first_pass_elements import (
    Block,
    CheckboxState,
    LatexBlock,
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

_INLINE_TYPES = (
    InlineLatex,
    Link,
    Verbatim,
    Code,
    Bold,
    Italic,
    Underline,
    StrikeThrough,
)

_CHECKBOX_MARK: dict[CheckboxState, str] = {
    CheckboxState.UNCHECKED: " ",
    CheckboxState.CHECKED: "X",
    CheckboxState.PARTIAL: "-",
}


def _render_property_drawer(drawer: PropertyDrawer | None) -> str:
    """Render a property drawer, verbatim when its source lines are kept."""
    if drawer is None:
        return ""
    if drawer.raw_lines:
        return "".join(drawer.raw_lines)

    indent = drawer.indent
    lines = [f"{indent}:PROPERTIES:\n"]
    for prop in drawer.node_properties:
        name = f"{prop.name}+" if prop.append else prop.name
        suffix = f" {prop.value}" if prop.value else ""
        lines.append(f"{indent}:{name}:{suffix}\n")
    lines.append(f"{indent}:END:\n")
    return "".join(lines)


def _render_block(block: Block) -> str:
    """Render a block, verbatim when its source lines are kept."""
    if block.raw_lines:
        return "".join(block.raw_lines)
    arguments = f" {block.arguments}" if block.arguments else ""
    return (
        f"#+begin_{block.name}{arguments}\n"
        f"{block.body}"
        f"#+end_{block.name}\n"
    )


def _render_list_item(item: ListItem) -> str:
    """Render a list item, verbatim when its source lines are kept."""
    if item.raw_lines:
        return "".join(item.raw_lines)
    if not item.lines:
        return ""

    first = item.lines[0]
    if len(item.lines) > 1 and not first.endswith("\n"):
        first = f"{first}\n"
    checkbox = (
        ""
        if item.checked is None
        else f"[{_CHECKBOX_MARK[item.checked]}] "
    )
    indent = " " * item.indent
    continuation = "".join(
        f"{indent}{line}" for line in item.lines[1:]
    )
    return f"{item.bullet} {checkbox}{first}{continuation}"


def _render_paragraph_text(text: ParagraphText) -> str:
    """Render paragraph text, falling back to its inline elements."""
    if text.text or not text.elements:
        return text.text
    return "".join(str(element) for element in text.elements)


def _render(node: object) -> str:
    """Render one AST node as Org-mode text."""
    match node:
        case Zettel():
            parts = [_render_property_drawer(node.properties)]
            if node.title:
                parts.append(f"#+title: {node.title}\n")
            if node.filetags:
                parts.append(f"#+filetags: {node.filetags}\n")
            parts.append(_render(node.body) if node.body else "")
            parts.extend(_render(child) for child in node.children)
            return "".join(parts)
        case Headline():
            parts = [f"{'*' * node.level} {node.title}\n"]
            parts.append(_render_property_drawer(node.properties))
            parts.append(_render(node.body) if node.body else "")
            parts.extend(_render(child) for child in node.children)
            return "".join(parts)
        case LatexBlock():
            return node.text
        case Block():
            return _render_block(node)
        case FlatText():
            return "".join(_render(element) for element in node.elements)
        case Paragraph():
            return "".join(_render(element) for element in node.elements)
        case ParagraphText():
            return _render_paragraph_text(node)
        case List():
            return "".join(_render(element) for element in node.elements)
        case ListItem():
            return _render_list_item(node)
        case BlankLines():
            return node.text
        case _ if isinstance(node, _INLINE_TYPES):
            return str(node)
        case PropertyDrawer():
            return _render_property_drawer(node)
        case _:
            raise TypeError(
                f"Cannot render object of type {type(node).__name__}"
            )


def to_org(node: object) -> str:
    """Render an AST node as best-effort Org-mode text.

    Args:
        node: The AST node to render.

    Returns:
        The reconstructed document text.
    """
    return _render(node)


__all__ = ["to_org"]
