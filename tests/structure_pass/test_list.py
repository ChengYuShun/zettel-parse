"""Tests for the List structure pass element."""

from __future__ import annotations

from zettel_parser.first_pass import parse_first_pass
from zettel_parser.first_pass_elements import ListItem as FirstPassListItem
from zettel_parser.structure_pass import Cursor
from zettel_parser.structure_pass_elements import List


def _parse(doc: str) -> tuple[List, Cursor]:
    cursor = Cursor(parse_first_pass(doc))
    result = List.try_parse(cursor)
    assert result is not None
    return result, cursor


def _kinds(lst: List) -> list[str]:
    return [type(element).__name__ for element in lst.elements]


def test_returns_none_without_consuming() -> None:
    cursor = Cursor(["text\n"])
    assert List.try_parse(cursor) is None
    assert cursor.index == 0

    cursor = Cursor([])
    assert List.try_parse(cursor) is None
    assert cursor.index == 0


def test_returns_none_when_starting_with_blank_lines() -> None:
    cursor = Cursor(parse_first_pass("\n- one\n"))
    assert List.try_parse(cursor) is None
    assert cursor.index == 0


def test_single_item_list() -> None:
    lst, cursor = _parse("- one\n")
    assert len(lst) == 1
    assert lst.bullet_type == "-"
    assert _kinds(lst) == ["ListItem"]
    assert cursor.index == 1


def test_adjacent_items() -> None:
    lst, cursor = _parse("- one\n- two\n- three\n")
    assert len(lst) == 3
    assert [item.lines for item in lst] == [["one\n"], ["two\n"], ["three\n"]]
    assert _kinds(lst) == ["ListItem", "ListItem", "ListItem"]
    assert cursor.index == 3


def test_access_nth_item() -> None:
    lst, _ = _parse("- one\n- two\n- three\n")
    assert lst[0].lines == ["one\n"]
    assert lst[1].lines == ["two\n"]
    assert lst[2].lines == ["three\n"]
    assert lst.items[0].lines == ["one\n"]
    assert [item.lines for item in lst] == [["one\n"], ["two\n"], ["three\n"]]


def test_ordered_items_with_skipped_numbers() -> None:
    lst, cursor = _parse("1. one\n3. three\n")
    assert len(lst) == 2
    assert lst.bullet_type == "."
    assert [item.lines for item in lst] == [["one\n"], ["three\n"]]
    assert cursor.index == 2


def test_blank_lines_between_items() -> None:
    lst, cursor = _parse("- one\n\n- two\n")
    assert _kinds(lst) == ["ListItem", "BlankLines", "ListItem"]
    assert len(lst) == 2
    assert str(lst) == "- one\n\n- two\n"
    assert cursor.index == 3


def test_multiple_blank_lines_between_items() -> None:
    lst, cursor = _parse("- one\n\n\n- two\n")
    assert _kinds(lst) == ["ListItem", "BlankLines", "ListItem"]
    assert cursor.index == 4


def test_trailing_blank_lines_not_consumed() -> None:
    lst, cursor = _parse("- one\n\n")
    assert _kinds(lst) == ["ListItem"]
    assert cursor.index == 1
    assert cursor.current == "\n"


def test_blank_lines_before_different_type_not_consumed() -> None:
    lst, cursor = _parse("- one\n\n+ two\n")
    assert _kinds(lst) == ["ListItem"]
    assert cursor.index == 1
    assert cursor.current == "\n"


def test_different_bullet_type_stops_list() -> None:
    cursor = Cursor(parse_first_pass("- one\n+ two\n"))
    lst = List.try_parse(cursor)
    assert lst is not None
    assert len(lst) == 1
    assert cursor.index == 1
    assert isinstance(cursor.current, FirstPassListItem)

    other = List.try_parse(cursor)
    assert other is not None
    assert other.bullet_type == "+"
    assert other[0].lines == ["two\n"]


def test_ordered_and_unordered_are_different_types() -> None:
    cursor = Cursor(parse_first_pass("- one\n1. two\n"))
    lst = List.try_parse(cursor)
    assert lst is not None
    assert len(lst) == 1
    assert cursor.index == 1


def test_item_with_continuation() -> None:
    lst, cursor = _parse("- one\n  continued\n- two\n")
    assert len(lst) == 2
    assert lst[0].lines == ["one\n", "continued\n"]
    assert lst[1].lines == ["two\n"]
    assert cursor.index == 3
