"""First pass tests for checklist (checkbox) parsing."""

from __future__ import annotations

from zettel_parser.first_pass import Cursor, ListItem, parse_first_pass
from zettel_parser.first_pass_elements import parse_checkbox


def test_unchecked_checkbox_alone() -> None:
    (element,) = parse_first_pass("- [ ]\n")
    assert isinstance(element, ListItem)
    assert element.checked is False
    assert element.value == ""


def test_checked_checkbox_alone() -> None:
    (element,) = parse_first_pass("- [X]\n")
    assert isinstance(element, ListItem)
    assert element.checked is True
    assert element.value == ""


def test_checkbox_with_text() -> None:
    (element,) = parse_first_pass("- [ ] task\n")
    assert isinstance(element, ListItem)
    assert element.checked is False
    assert element.value == "task"

    (element,) = parse_first_pass("- [X] done\n")
    assert isinstance(element, ListItem)
    assert element.checked is True
    assert element.value == "done"


def test_checkbox_removes_exactly_one_following_space() -> None:
    (element,) = parse_first_pass("- [X]  spaced\n")
    assert isinstance(element, ListItem)
    assert element.checked is True
    assert element.value == " spaced"


def test_checkbox_trailing_whitespace_is_ignored() -> None:
    (element,) = parse_first_pass("- [X]   \n")
    assert isinstance(element, ListItem)
    assert element.checked is True
    assert element.value == ""


def test_checkbox_after_ordered_bullet() -> None:
    (element,) = parse_first_pass("1. [X] done\n")
    assert isinstance(element, ListItem)
    assert element.checked is True
    assert element.value == "done"
    assert element.ordered is True


def test_checkbox_after_all_bullet_variants() -> None:
    for bullet, mark, expected in (("+", " ", False), ("*", "X", True)):
        element = ListItem.try_parse(Cursor([f"{bullet} [{mark}] item\n"]))
        assert isinstance(element, ListItem)
        assert element.checked is expected
        assert element.value == "item"


def test_marker_not_followed_by_space_is_plain_text() -> None:
    for line, value in (
        ("- [ ]x\n", "[ ]x"),
        ("- [X]extra\n", "[X]extra"),
        ("- [X]\ttext\n", "[X]\ttext"),
    ):
        (element,) = parse_first_pass(line)
        assert isinstance(element, ListItem)
        assert element.checked is None
        assert element.value == value


def test_lowercase_x_is_not_a_marker() -> None:
    (element,) = parse_first_pass("- [x] task\n")
    assert isinstance(element, ListItem)
    assert element.checked is None
    assert element.value == "[x] task"


def test_item_without_checkbox_has_no_state() -> None:
    (element,) = parse_first_pass("- item\n")
    assert isinstance(element, ListItem)
    assert element.checked is None
    assert element.value == "item"


def test_parse_checkbox_helper() -> None:
    assert parse_checkbox("[X] done") == (True, "done")
    assert parse_checkbox("[ ]") == (False, "")
    assert parse_checkbox("[X] ") == (True, "")
    assert parse_checkbox("[ ]  spaced") == (False, " spaced")
    assert parse_checkbox("plain") == (None, "plain")
    assert parse_checkbox("[ ]x") == (None, "[ ]x")
