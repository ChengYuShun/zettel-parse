"""Tests for the FlatText structure pass element."""

from __future__ import annotations

from zettel_parser.first_pass_elements import Headline, Title
from zettel_parser.structure_pass import Cursor
from zettel_parser.structure_pass_elements import (
    BlankLines,
    FlatText,
    Paragraph,
)


def _kinds(flat_text: FlatText) -> list[str]:
    return [type(element).__name__ for element in flat_text.elements]


def test_single_paragraph_without_trailing_blanks() -> None:
    cursor = Cursor(["line one\n", "line two\n"])
    flat_text = FlatText.try_parse(cursor)
    assert flat_text is not None
    assert _kinds(flat_text) == ["Paragraph"]
    assert flat_text.paragraphs == [Paragraph(["line one\n", "line two\n"])]
    assert str(flat_text) == "line one\nline two\n"
    assert cursor.index == 2


def test_paragraphs_with_separating_blanks_only() -> None:
    cursor = Cursor(["p1\n", "\n", "p2\n", "\n", "p3\n"])
    flat_text = FlatText.try_parse(cursor)
    assert flat_text is not None
    assert _kinds(flat_text) == [
        "Paragraph",
        "BlankLines",
        "Paragraph",
        "BlankLines",
        "Paragraph",
    ]
    assert len(flat_text.paragraphs) == 3
    assert str(flat_text) == "p1\n\np2\n\np3\n"
    assert cursor.index == 5


def test_paragraphs_with_trailing_blanks() -> None:
    cursor = Cursor(["p1\n", "\n", "\n", "p2\n", "\n"])
    flat_text = FlatText.try_parse(cursor)
    assert flat_text is not None
    assert _kinds(flat_text) == [
        "Paragraph",
        "BlankLines",
        "Paragraph",
        "BlankLines",
    ]
    assert len(flat_text.paragraphs) == 2
    assert str(flat_text) == "p1\n\n\np2\n\n"
    assert cursor.index == 5


def test_stops_at_non_fitting_element_with_trailing_blanks() -> None:
    headline = Headline(level=1, title="Title", raw_line="* Title\n")
    cursor = Cursor(["p1\n", "\n", headline, "after\n"])
    flat_text = FlatText.try_parse(cursor)
    assert flat_text is not None
    assert _kinds(flat_text) == ["Paragraph", "BlankLines"]
    assert cursor.index == 2
    assert cursor.current is headline


def test_returns_none_when_starting_with_blank_lines() -> None:
    cursor = Cursor(["\n", "p1\n"])
    assert FlatText.try_parse(cursor) is None
    assert cursor.index == 0


def test_returns_none_when_not_starting_with_paragraph() -> None:
    cursor = Cursor([Title(value="Doc", raw_line="#+title: Doc\n"), "p1\n"])
    assert FlatText.try_parse(cursor) is None
    assert cursor.index == 0

    cursor = Cursor([])
    assert FlatText.try_parse(cursor) is None


def test_stops_at_non_fitting_element_without_blanks() -> None:
    headline = Headline(level=1, title="Title", raw_line="* Title\n")
    cursor = Cursor(["p1\n", headline])
    flat_text = FlatText.try_parse(cursor)
    assert flat_text is not None
    assert _kinds(flat_text) == ["Paragraph"]
    assert cursor.current is headline


def test_flat_text_part_union_members() -> None:
    cursor = Cursor(["p1\n", "\n"])
    flat_text = FlatText.try_parse(cursor)
    assert flat_text is not None
    assert isinstance(flat_text.elements[0], Paragraph)
    assert isinstance(flat_text.elements[1], BlankLines)
