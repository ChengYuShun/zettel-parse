"""Tests for the blank line regular expression in common_regex."""

from __future__ import annotations

from zettel_parser.common_regex import BLANK_LINE


def test_empty_line_is_blank() -> None:
    assert BLANK_LINE.match("") is not None
    assert BLANK_LINE.match("\n") is not None
    assert BLANK_LINE.match("\r\n") is not None


def test_whitespace_only_line_is_blank() -> None:
    assert BLANK_LINE.match("   \n") is not None
    assert BLANK_LINE.match("\t\t\n") is not None
    assert BLANK_LINE.match(" \t \t \n") is not None


def test_line_with_text_is_not_blank() -> None:
    assert BLANK_LINE.match("text\n") is None
    assert BLANK_LINE.match("  x\n") is None
    assert BLANK_LINE.match("x  \n") is None


def test_blank_line_with_carriage_return_and_trailing_spaces() -> None:
    assert BLANK_LINE.match("  \r\n") is not None
