"""Tests for checklists in the ListItem structure pass element."""

from __future__ import annotations

from zettel_parser.first_pass import parse_first_pass
from zettel_parser.first_pass_elements import CheckboxState
from zettel_parser.structure_pass import Cursor
from zettel_parser.structure_pass_elements import List, ListItem, Paragraph


def _parse(doc: str) -> tuple[ListItem, Cursor]:
    cursor = Cursor(parse_first_pass(doc))
    item = ListItem.try_parse(cursor)
    assert item is not None
    return item, cursor


def test_checked_item() -> None:
    item, cursor = _parse("- [X] done\n")
    assert item.checked is CheckboxState.CHECKED
    assert item.lines == ["done\n"]
    assert item.body is not None
    assert str(item.body) == "done\n"
    assert cursor.index == 1


def test_unchecked_item() -> None:
    item, _ = _parse("- [ ] task\n")
    assert item.checked is CheckboxState.UNCHECKED
    assert item.lines == ["task\n"]


def test_partial_item() -> None:
    item, _ = _parse("- [-] partial\n")
    assert item.checked is CheckboxState.PARTIAL
    assert item.lines == ["partial\n"]


def test_bare_checked_item_body_is_blank_lines() -> None:
    item, _ = _parse("- [X]\n")
    assert item.checked is CheckboxState.CHECKED
    assert item.lines == ["\n"]
    assert item.body is not None
    assert [type(element).__name__ for element in item.body.elements] == [
        "BlankLines"
    ]


def test_checkbox_with_continuation_lines() -> None:
    item, _ = _parse("- [X] first\n  second\n")
    assert item.checked is CheckboxState.CHECKED
    assert item.lines == ["first\n", "second\n"]


def test_checkbox_with_blank_line_between_continuations() -> None:
    item, _ = _parse("- [ ] a\n\n  b\n")
    assert item.checked is CheckboxState.UNCHECKED
    assert item.lines == ["a\n", "\n", "b\n"]


def test_extra_spaces_before_marker_prevent_checkbox() -> None:
    item, _ = _parse("-   [X] done\n")
    assert item.checked is None
    assert item.lines == ["  [X] done\n"]


def test_marker_not_followed_by_space_is_plain() -> None:
    item, _ = _parse("- [ ]x\n")
    assert item.checked is None
    assert item.lines == ["[ ]x\n"]


def test_raw_line_is_preserved() -> None:
    doc = "- [X] done\n"
    item, _ = _parse(doc)
    assert str(item) == doc
    assert item.raw_lines == [doc]


def test_nested_checklists() -> None:
    item, _ = _parse("- [X] parent\n  - [ ] child\n")
    assert item.checked is CheckboxState.CHECKED
    assert item.body is not None
    paragraph = item.body.elements[0]
    assert isinstance(paragraph, Paragraph)
    nested = paragraph.elements[1]
    assert isinstance(nested, List)
    assert nested[0].checked is CheckboxState.UNCHECKED
    assert nested[0].lines == ["child\n"]
