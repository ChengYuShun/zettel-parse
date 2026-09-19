"""Tests for the ListItem structure pass element."""

from __future__ import annotations

from zettel_parser.first_pass import parse_first_pass
from zettel_parser.first_pass_elements import (
    Block,
    Headline,
    LatexBlock,
    ListItem as FirstPassListItem,
)
from zettel_parser.structure_pass import Cursor
from zettel_parser.structure_pass_elements import ListItem, Paragraph


def _parse(doc: str) -> tuple[ListItem, Cursor]:
    cursor = Cursor(parse_first_pass(doc))
    item = ListItem.try_parse(cursor)
    assert item is not None
    return item, cursor


def test_returns_none_without_consuming() -> None:
    cursor = Cursor(["plain text\n"])
    assert ListItem.try_parse(cursor) is None
    assert cursor.index == 0

    cursor = Cursor([])
    assert ListItem.try_parse(cursor) is None
    assert cursor.index == 0


def test_simple_single_line_item() -> None:
    doc = "- item one\n"
    item, cursor = _parse(doc)
    assert item.bullet == "-"
    assert item.value == "item one"
    assert item.lines == ["item one\n"]
    assert item.raw_lines == ["- item one\n"]
    assert str(item) == doc
    assert cursor.index == 1


def test_item_line_is_first_in_collected_lines() -> None:
    item, _ = _parse("- item\n  more\n")
    assert item.lines == ["item\n", "more\n"]


def test_ordered_item_line_has_bullet_removed() -> None:
    item, _ = _parse("10. item\n    continuation\n")
    assert item.lines == ["item\n", "continuation\n"]


def test_item_line_removes_only_bullet_and_one_space() -> None:
    item, _ = _parse("-   item\n")
    assert item.lines == ["  item\n"]


def test_bare_bullet_line_becomes_empty_line() -> None:
    item, _ = _parse("-\n")
    assert item.lines == ["\n"]

    item, _ = _parse("-")
    assert item.lines == [""]


def test_indented_continuation_lines() -> None:
    doc = "- item\n  continuation one\n  continuation two\n"
    item, cursor = _parse(doc)
    assert item.lines == ["item\n", "continuation one\n", "continuation two\n"]
    assert str(item) == doc
    assert cursor.index == 3


def test_extra_indentation_is_preserved() -> None:
    doc = "- item\n    lots of space\n"
    item, _ = _parse(doc)
    assert item.lines == ["item\n", "  lots of space\n"]


def test_indent_is_based_on_bullet_width() -> None:
    doc = "10. item\n    continuation\n   short\n"
    item, cursor = _parse(doc)
    assert item.indent == 4
    assert item.lines == ["item\n", "continuation\n"]
    assert cursor.index == 2


def test_blank_line_between_continuations() -> None:
    doc = "- item\n  a\n\n  b\n"
    item, cursor = _parse(doc)
    assert item.lines == ["item\n", "a\n", "\n", "b\n"]
    assert str(item) == doc
    assert cursor.index == 4


def test_blank_line_keeps_spaces_beyond_indent() -> None:
    doc = "- item\n  a\n    \n  b\n"
    item, _ = _parse(doc)
    assert item.lines == ["item\n", "a\n", "  \n", "b\n"]


def test_trailing_blank_line_not_consumed() -> None:
    doc = "- item\n  a\n\nnot indented\n"
    item, cursor = _parse(doc)
    assert item.lines == ["item\n", "a\n"]
    assert cursor.index == 2
    assert cursor.current == "\n"


def test_trailing_blank_lines_at_eof_not_consumed() -> None:
    cursor = Cursor(parse_first_pass("- item\n  a\n\n"))
    item = ListItem.try_parse(cursor)
    assert item is not None
    assert item.lines == ["item\n", "a\n"]
    assert cursor.index == 2


def test_blank_lines_before_non_plain_element_not_consumed() -> None:
    cursor = Cursor(parse_first_pass("- item\n\n* Head\n"))
    item = ListItem.try_parse(cursor)
    assert item is not None
    assert item.lines == ["item\n"]
    assert cursor.index == 1
    assert cursor.current == "\n"


def test_lower_indentation_stops_item() -> None:
    doc = "- item\n not enough\n"
    item, cursor = _parse(doc)
    assert item.lines == ["item\n"]
    assert cursor.index == 1


def test_tab_indentation_does_not_count() -> None:
    doc = "- item\n\tcontinuation\n"
    item, cursor = _parse(doc)
    assert item.lines == ["item\n"]
    assert cursor.index == 1


def test_stops_at_next_list_item() -> None:
    cursor = Cursor(parse_first_pass("- one\n- two\n"))
    first = ListItem.try_parse(cursor)
    assert first is not None
    assert first.value == "one"
    assert first.lines == ["one\n"]
    assert cursor.index == 1
    assert isinstance(cursor.current, FirstPassListItem)

    second = ListItem.try_parse(cursor)
    assert second is not None
    assert second.value == "two"
    assert cursor.index == 2


def test_stops_at_non_plain_element() -> None:
    cursor = Cursor(
        [FirstPassListItem(bullet="-", value="item", raw_line="- item\n"),
         Headline(level=1, title="Head", raw_line="* Head\n")]
    )
    item = ListItem.try_parse(cursor)
    assert item is not None
    assert item.lines == ["item\n"]
    assert cursor.index == 1


def test_cursor_strings_remain_intact() -> None:
    raw = ["- item\n", "  a\n", "\n", "  b\n", "tail\n"]
    cursor = Cursor(parse_first_pass("".join(raw)))
    before = list(cursor.elements)
    item = ListItem.try_parse(cursor)
    assert item is not None
    assert cursor.elements == before
    assert cursor.elements[1] == "  a\n"
    assert cursor.elements[3] == "  b\n"


def test_body_is_flat_text_of_paragraphs() -> None:
    item, _ = _parse("- item\n  first\n\n  second\n")
    assert item.body is not None
    assert [type(element).__name__ for element in item.body.elements] == [
        "Paragraph",
        "BlankLines",
        "Paragraph",
    ]
    assert str(item.body) == "item\nfirst\n\nsecond\n"


def test_body_from_item_line_without_continuation() -> None:
    item, _ = _parse("- item\n")
    assert item.body is not None
    assert [type(element).__name__ for element in item.body.elements] == [
        "Paragraph"
    ]
    assert str(item.body) == "item\n"


def test_body_of_bare_bullet_is_blank_lines() -> None:
    item, _ = _parse("-\n")
    assert item.lines == ["\n"]
    assert item.body is not None
    assert [type(element).__name__ for element in item.body.elements] == [
        "BlankLines"
    ]


def test_body_contains_block() -> None:
    item, _ = _parse("- item\n  #+begin_src python\n  x = 1\n  #+end_src\n")
    assert item.body is not None
    paragraph = item.body.elements[0]
    assert isinstance(paragraph, Paragraph)
    assert isinstance(paragraph.elements[1], Block)
    assert paragraph.elements[1].name == "src"
    assert paragraph.elements[1].body == "x = 1\n"


def test_body_contains_latex_block() -> None:
    item, _ = _parse("- item\n  \\[\n  x\n  \\]\n")
    assert item.body is not None
    paragraph = item.body.elements[0]
    assert isinstance(paragraph, Paragraph)
    assert isinstance(paragraph.elements[1], LatexBlock)
    assert paragraph.elements[1].text == "\\[\nx\n\\]\n"


def test_body_stops_at_nested_list_item() -> None:
    item, _ = _parse("- parent\n  paragraph\n  - nested\n")
    assert item.lines == ["parent\n", "paragraph\n", "- nested\n"]
    assert item.body is not None
    assert [type(element).__name__ for element in item.body.elements] == [
        "Paragraph"
    ]
    assert str(item.body) == "parent\nparagraph\n"


def test_body_from_item_line_when_nested_list_follows() -> None:
    item, _ = _parse("- parent\n  - nested\n")
    assert item.lines == ["parent\n", "- nested\n"]
    assert item.body is not None
    assert [type(element).__name__ for element in item.body.elements] == [
        "Paragraph"
    ]
    assert str(item.body) == "parent\n"


def test_body_treats_other_keywords_as_plain_lines() -> None:
    item, _ = _parse(
        "- item\n  #+title: Not a title\n  #+filetags: :a:\n"
    )
    assert item.body is not None
    assert [type(element).__name__ for element in item.body.elements] == [
        "Paragraph"
    ]
    paragraph = item.body.elements[0]
    assert isinstance(paragraph, Paragraph)
    assert [type(element).__name__ for element in paragraph.elements] == [
        "str",
        "str",
        "str",
    ]
