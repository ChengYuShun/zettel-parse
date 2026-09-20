"""Tests for nested lists produced through list item bodies."""

from __future__ import annotations

from zettel_parser.first_pass import parse_first_pass
from zettel_parser.structure_pass import Cursor
from zettel_parser.structure_pass_elements import (
    List,
    ListItem,
    Paragraph,
    ParagraphText,
)


def _parse_item(doc: str) -> ListItem:
    cursor = Cursor(parse_first_pass(doc))
    item = ListItem.try_parse(cursor)
    assert item is not None
    return item


def _body_paragraph(item: ListItem) -> Paragraph:
    assert item.body is not None
    paragraph = item.body.elements[0]
    assert isinstance(paragraph, Paragraph)
    return paragraph


def test_single_level_nesting() -> None:
    item = _parse_item("- parent\n  - child\n")
    paragraph = _body_paragraph(item)
    assert paragraph.elements[0] == ParagraphText("parent\n")
    nested = paragraph.elements[1]
    assert isinstance(nested, List)
    assert len(nested) == 1
    assert nested[0].value == "child"


def test_sibling_nested_items_form_one_list() -> None:
    item = _parse_item("- parent\n  - a\n  - b\n")
    paragraph = _body_paragraph(item)
    nested = paragraph.elements[1]
    assert isinstance(nested, List)
    assert len(nested) == 2
    assert [child.value for child in nested] == ["a", "b"]


def test_nested_list_with_blank_lines() -> None:
    item = _parse_item("- parent\n  - a\n\n  - b\n")
    paragraph = _body_paragraph(item)
    nested = paragraph.elements[1]
    assert isinstance(nested, List)
    assert len(nested) == 2
    assert [type(element).__name__ for element in nested.elements] == [
        "ListItem",
        "BlankLines",
        "ListItem",
    ]


def test_ordered_nested_list_with_skipped_numbers() -> None:
    item = _parse_item("- parent\n  1. a\n  3. b\n")
    paragraph = _body_paragraph(item)
    nested = paragraph.elements[1]
    assert isinstance(nested, List)
    assert nested.bullet_type == "."
    assert [child.value for child in nested] == ["a", "b"]


def test_deeply_nested_lists() -> None:
    item = _parse_item("- a\n  - b\n    - c\n")
    paragraph = _body_paragraph(item)
    outer = paragraph.elements[1]
    assert isinstance(outer, List)
    assert outer[0].value == "b"

    inner_paragraph = _body_paragraph(outer[0])
    inner = inner_paragraph.elements[1]
    assert isinstance(inner, List)
    assert inner[0].value == "c"


def test_text_surrounding_nested_list() -> None:
    item = _parse_item("- parent\n  before\n  - child\n  after\n")
    paragraph = _body_paragraph(item)
    assert [type(element).__name__ for element in paragraph.elements] == [
        "ParagraphText",
        "List",
        "ParagraphText",
    ]
    assert paragraph.elements[0] == ParagraphText("parent\nbefore\n")
    assert isinstance(paragraph.elements[1], List)
    assert paragraph.elements[2] == ParagraphText("after\n")


def test_nested_list_of_different_bullet_after_paragraph() -> None:
    item = _parse_item("- parent\n  - a\n  + b\n")
    paragraph = _body_paragraph(item)
    assert [type(element).__name__ for element in paragraph.elements] == [
        "ParagraphText",
        "List",
        "List",
    ]
    first, second = paragraph.elements[1], paragraph.elements[2]
    assert isinstance(first, List)
    assert isinstance(second, List)
    assert first.bullet_type == "-"
    assert second.bullet_type == "+"
