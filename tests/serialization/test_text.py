"""Tests for the snapshot-style text renderer."""

from __future__ import annotations

from zettel_parser.serialization import to_text
from zettel_parser.structure_pass import parse


def test_text_outline() -> None:
    text = to_text(parse("#+title: Doc\n\nHello *world*\n"))
    assert text == (
        "Zettel title='Doc' filetags=''\n"
        "  FlatText\n"
        "    BlankLines x1\n"
        "    Paragraph\n"
        "      ParagraphText\n"
        "        str 'Hello '\n"
        "        Bold\n"
        "          str 'world'\n"
        "        str '\\n'\n"
    )


def test_output_ends_with_a_single_newline() -> None:
    text = to_text(parse("text\n"))
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_output_is_deterministic() -> None:
    ast = parse("- one\n- two\n")
    assert to_text(ast) == to_text(ast)
