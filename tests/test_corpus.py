"""File-based tests over the editable corpus in ``tests/corpus``.

Every ``*.org`` file in that directory is discovered automatically.  Each one
is checked with an exact source round-trip through the first pass and a
structure snapshot of the full AST.  Add or edit corpus files freely, then
refresh the snapshots with ``pytest --snapshot-update``.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import pytest
from syrupy.assertion import SnapshotAssertion
from syrupy.extensions.amber import AmberSnapshotExtension

from zettel_parser.first_pass import parse_first_pass
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
from zettel_parser.structure_pass import parse
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

CORPUS_DIR = Path(__file__).parent / "corpus"
ORG_FILES = sorted(CORPUS_DIR.glob("*.org"))

if not ORG_FILES:
    pytest.skip("no corpus files yet", allow_module_level=True)

_INDENT = "  "


class RawTextSnapshotExtension(AmberSnapshotExtension):
    """Store strings verbatim so snapshots read as the AST outline itself."""

    def serialize(self, data: Any, **kwargs: Any) -> str:
        if isinstance(data, str):
            return data
        return super().serialize(data, **kwargs)


@pytest.fixture
def ast_snapshot(snapshot: SnapshotAssertion) -> SnapshotAssertion:
    """A snapshot that writes raw text instead of a quoted representation."""
    return snapshot.use_extension(RawTextSnapshotExtension)


def _render_first_pass(source: str) -> str:
    """Reconstruct the source text from the first-pass elements."""
    return "".join(str(element) for element in parse_first_pass(source))


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
    if drawer is not None:
        _emit(lines, depth, f"Properties {list(drawer.keys())}")


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
            _emit(lines, depth, f"LatexBlock type={node.type.name}")
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


def describe(node: object) -> str:
    """Return a compact, deterministic outline of a parsed AST.

    Only node types and salient scalar values are included, so the result is
    stable across edits to raw text, whitespace, and line endings.
    """
    lines: list[str] = []
    _describe(node, 0, lines)
    return "\n".join(lines) + "\n"


@pytest.mark.parametrize("org_file", ORG_FILES, ids=lambda path: path.stem)
def test_source_roundtrips(org_file: Path) -> None:
    """The first pass must reproduce the source text exactly."""
    source = org_file.read_text(encoding="utf-8")
    assert _render_first_pass(source) == source


@pytest.mark.parametrize("org_file", ORG_FILES, ids=lambda path: path.stem)
def test_structure_snapshot(
    org_file: Path, ast_snapshot: SnapshotAssertion
) -> None:
    """The parsed structure must match the committed snapshot."""
    source = org_file.read_text(encoding="utf-8")
    assert ast_snapshot == describe(parse(source))


@pytest.mark.parametrize("org_file", ORG_FILES, ids=lambda path: path.stem)
def test_reparse_is_stable(org_file: Path) -> None:
    """Re-parsing the reconstructed source yields the same structure."""
    source = org_file.read_text(encoding="utf-8")
    assert describe(parse(source)) == describe(parse(_render_first_pass(source)))
