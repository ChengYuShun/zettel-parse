"""First pass tests for list item parsing."""

from __future__ import annotations

from zettel_parser.first_pass import Cursor, ListItem, parse_first_pass


def test_parse_unordered_list_item() -> None:
    (element,) = parse_first_pass("- first\n")
    assert isinstance(element, ListItem)
    assert element.bullet == "-"
    assert element.value == "first"
    assert element.ordered is False


def test_parse_ordered_list_items() -> None:
    elements = parse_first_pass("1. first\n2) second\n10. third\n")
    assert all(isinstance(e, ListItem) for e in elements)
    bullets = [e.bullet for e in elements if isinstance(e, ListItem)]
    assert bullets == ["1.", "2)", "10."]
    assert all(e.ordered for e in elements if isinstance(e, ListItem))


def test_parse_bullet_may_end_line() -> None:
    for line, bullet in (
        ("-\n", "-"),
        ("+\n", "+"),
        ("1.\n", "1."),
        ("1)\n", "1)"),
    ):
        (element,) = parse_first_pass(line)
        assert isinstance(element, ListItem)
        assert element.bullet == bullet
        assert element.value == ""


def test_parse_bullet_at_end_of_input() -> None:
    for bullet in ("-", "+", "1.", "1)"):
        (element,) = parse_first_pass(bullet)
        assert isinstance(element, ListItem)
        assert element.bullet == bullet
        assert element.value == ""
        assert element.raw_line == bullet


def test_bullet_without_space_is_not_list_item() -> None:
    lines = ["-item\n", "+item\n", "1.item\n", "1)item\n"]
    assert parse_first_pass(lines) == lines


def test_alpha_bullets_are_not_list_items() -> None:
    lines = ["a. item\n", "A) item\n", "z) item\n"]
    assert parse_first_pass(lines) == lines


def test_list_item_description_value() -> None:
    (element,) = parse_first_pass("- term :: definition\n")
    assert isinstance(element, ListItem)
    assert element.value == "term :: definition"


def test_list_item_among_other_structures() -> None:
    doc = "#+title: Doc\n* Heading\n- item\n"
    elements = parse_first_pass(doc)
    items = [e for e in elements if isinstance(e, ListItem)]
    assert len(items) == 1
    assert items[0].value == "item"


def test_list_item_does_not_absorb_following_lines() -> None:
    doc = "- item\n  continued\n"
    elements = parse_first_pass(doc)
    assert len(elements) == 2
    assert isinstance(elements[0], ListItem)
    assert elements[1] == "  continued\n"


def test_indented_list_item_is_plain() -> None:
    lines = ["  - item\n"]
    assert parse_first_pass(lines) == lines


def test_list_item_from_bytes() -> None:
    (element,) = parse_first_pass(b"- item\r\n")
    assert isinstance(element, ListItem)
    assert element.value == "item"


def test_list_item_try_parse_with_bullets() -> None:
    cursor = Cursor(["- item\n"])
    item = ListItem.try_parse_with_bullets(cursor, {"-"})
    assert isinstance(item, ListItem)
    assert item.bullet == "-"
    assert item.value == "item"
    assert cursor.index == 1

    cursor = Cursor(["  - indented\n"])
    assert ListItem.try_parse_with_bullets(cursor, {"-"}) is None
    assert cursor.index == 0


def test_list_item_try_parse_with_bullets_selects_kinds() -> None:
    cursor = Cursor(["+ item\n"])
    assert ListItem.try_parse_with_bullets(cursor, {"-"}) is None
    assert cursor.index == 0

    cursor = Cursor(["2) item\n"])
    assert ListItem.try_parse_with_bullets(cursor, {"."}) is None
    assert cursor.index == 0

    cursor = Cursor(["2) item\n"])
    item = ListItem.try_parse_with_bullets(cursor, {")"})
    assert isinstance(item, ListItem)
    assert item.bullet == "2)"

    cursor = Cursor(["* item\n"])
    assert ListItem.try_parse_with_bullets(cursor, {"-", "+", ".", ")"}) is None
    assert cursor.index == 0

    cursor = Cursor(["* item\n"])
    item = ListItem.try_parse_with_bullets(cursor, {"*"})
    assert isinstance(item, ListItem)
    assert item.bullet == "*"
