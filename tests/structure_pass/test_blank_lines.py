"""Tests for the BlankLines structure pass element."""

from __future__ import annotations

from zettel_parser.first_pass_elements import Headline
from zettel_parser.structure_pass import Cursor
from zettel_parser.structure_pass_elements import BlankLines


def test_single_blank_line() -> None:
    cursor = Cursor(["\n", "text\n"])
    blank_lines = BlankLines.try_parse(cursor)
    assert blank_lines is not None
    assert blank_lines.text == "\n"
    assert blank_lines.count == 1
    assert str(blank_lines) == "\n"
    assert cursor.index == 1


def test_run_of_blank_lines() -> None:
    raw = ["\n", "   \n", "\t\t\n", "\r\n"]
    cursor = Cursor([*raw, "text\n"])
    blank_lines = BlankLines.try_parse(cursor)
    assert blank_lines is not None
    assert blank_lines.text == "".join(raw)
    assert blank_lines.count == 4
    assert str(blank_lines) == "".join(raw)
    assert cursor.index == 4


def test_stops_at_first_non_blank_line() -> None:
    cursor = Cursor(["\n", "text\n", "\n"])
    blank_lines = BlankLines.try_parse(cursor)
    assert blank_lines is not None
    assert blank_lines.text == "\n"
    assert cursor.index == 1


def test_returns_none_without_consuming() -> None:
    cursor = Cursor(["text\n", "\n"])
    assert BlankLines.try_parse(cursor) is None
    assert cursor.index == 0


def test_returns_none_on_non_string_element() -> None:
    cursor = Cursor([Headline(level=1, title="Title", raw_line="* Title\n")])
    assert BlankLines.try_parse(cursor) is None
    assert cursor.index == 0


def test_returns_none_at_end() -> None:
    cursor = Cursor([])
    assert BlankLines.try_parse(cursor) is None
    assert cursor.index == 0
