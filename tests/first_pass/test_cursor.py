"""Tests for the cursor used by the parsing passes."""

from __future__ import annotations

from zettel_parser.first_pass import Cursor


def test_cursor_navigation() -> None:
    cursor: Cursor[str] = Cursor(["a\n", "b\n"])
    assert cursor.current == "a\n"
    assert cursor.peek() == "a\n"
    assert cursor.peek(1) == "b\n"
    assert cursor.peek(5) is None
    assert cursor.peek(-1) is None
    assert not cursor.at_end

    cursor.advance()
    assert cursor.current == "b\n"
    cursor.advance()
    assert cursor.at_end
    assert cursor.current is None


def test_cursor_from_first_pass_module() -> None:
    from zettel_parser.cursor import Cursor as SharedCursor

    assert Cursor is SharedCursor
