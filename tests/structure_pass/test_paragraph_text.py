"""Tests for the ParagraphText structure pass element."""

from __future__ import annotations

from zettel_parser.first_pass_elements import Headline
from zettel_parser.structure_pass import Cursor
from zettel_parser.structure_pass_elements import ParagraphText


def test_single_line() -> None:
    cursor = Cursor(["hello\n"])
    text = ParagraphText.try_parse(cursor)
    assert text is not None
    assert text.text == "hello\n"
    assert str(text) == "hello\n"
    assert cursor.index == 1


def test_consecutive_lines_are_concatenated() -> None:
    cursor = Cursor(["foo\n", "bar\n", "baz\n"])
    text = ParagraphText.try_parse(cursor)
    assert text is not None
    assert text.text == "foo\nbar\nbaz\n"
    assert cursor.index == 3


def test_stops_at_blank_line() -> None:
    cursor = Cursor(["foo\n", "\n", "bar\n"])
    text = ParagraphText.try_parse(cursor)
    assert text is not None
    assert text.text == "foo\n"
    assert cursor.index == 1


def test_whitespace_is_preserved() -> None:
    cursor = Cursor(["  foo bar  \n"])
    text = ParagraphText.try_parse(cursor)
    assert text is not None
    assert text.text == "  foo bar  \n"


def test_stops_at_non_string_element() -> None:
    headline = Headline(level=1, title="Title", raw_line="* Title\n")
    cursor = Cursor(["foo\n", headline])
    text = ParagraphText.try_parse(cursor)
    assert text is not None
    assert text.text == "foo\n"
    assert cursor.index == 1


def test_returns_none_without_consuming_at_blank_line() -> None:
    cursor = Cursor(["\n"])
    assert ParagraphText.try_parse(cursor) is None
    assert cursor.index == 0


def test_returns_none_without_consuming_on_non_string() -> None:
    cursor = Cursor(
        [Headline(level=1, title="Title", raw_line="* Title\n")]
    )
    assert ParagraphText.try_parse(cursor) is None
    assert cursor.index == 0


def test_returns_none_at_end() -> None:
    cursor = Cursor([])
    assert ParagraphText.try_parse(cursor) is None
    assert cursor.index == 0
