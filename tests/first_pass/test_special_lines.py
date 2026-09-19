"""First pass tests for single-line parsing: titles, headlines, and lists."""

from __future__ import annotations

import io

from zettel_parser.common_regex import HEADLINE, LIST_ITEM, TITLE
from zettel_parser.first_pass import (
    Block,
    Headline,
    ListItem,
    PropertyDrawer,
    Title,
    parse_first_pass,
)


def test_title_regex() -> None:
    match = TITLE.match("#+title: My Document\n")
    assert match is not None
    assert match.group("value") == "My Document"

    match = TITLE.match("#+TITLE: Upper\n")
    assert match is not None
    assert match.group("value") == "Upper"

    match = TITLE.match("#+title:\n")
    assert match is not None
    assert match.group("value") == ""

    assert TITLE.match("  #+title: Indented\n") is None
    assert TITLE.match("#+titles: nope\n") is None


def test_title_regex_crlf_and_no_space() -> None:
    match = TITLE.match("#+title:NoSpace\r\n")
    assert match is not None
    assert match.group("value") == "NoSpace"


def test_headline_regex() -> None:
    match = HEADLINE.match("* Heading\n")
    assert match is not None
    assert match.group("stars") == "*"
    assert match.group("title") == "Heading"

    match = HEADLINE.match("*** Deep\n")
    assert match is not None
    assert match.group("stars") == "***"
    assert match.group("title") == "Deep"

    assert HEADLINE.match("**bold**\n") is None
    assert HEADLINE.match("*NoSpace\n") is None
    assert HEADLINE.match("  * Indented\n") is None


def test_list_item_regex_unordered() -> None:
    for bullet in ("-", "+"):
        match = LIST_ITEM.match(f"{bullet} item\n")
        assert match is not None
        assert match.group("bullet") == bullet
        assert match.group("value") == "item"


def test_list_item_regex_ordered() -> None:
    for bullet in ("1.", "1)", "10.", "42)"):
        match = LIST_ITEM.match(f"{bullet} item\n")
        assert match is not None
        assert match.group("bullet") == bullet
        assert match.group("value") == "item"


def test_list_item_regex_bullet_may_end_line() -> None:
    for bullet in ("-", "+", "1.", "1)"):
        match = LIST_ITEM.match(f"{bullet}\n")
        assert match is not None
        assert match.group("bullet") == bullet
        assert match.group("value") is None

        match = LIST_ITEM.match(bullet)
        assert match is not None
        assert match.group("bullet") == bullet
        assert match.group("value") is None


def test_list_item_regex_bullet_may_end_crlf_line() -> None:
    match = LIST_ITEM.match("-\r\n")
    assert match is not None
    assert match.group("bullet") == "-"
    assert match.group("value") is None


def test_list_item_regex_requires_space_or_line_end() -> None:
    for bullet in ("-", "+", "1.", "1)"):
        assert LIST_ITEM.match(f"{bullet}item\n") is None


def test_list_item_regex_rejects() -> None:
    assert LIST_ITEM.match("  - indented\n") is None
    assert LIST_ITEM.match("* star\n") is None
    assert LIST_ITEM.match("a. letter\n") is None
    assert LIST_ITEM.match("A) letter\n") is None
    assert LIST_ITEM.match("z) letter\n") is None
    assert LIST_ITEM.match("ab. two letters\n") is None
    assert LIST_ITEM.match("#+title: x\n") is None


def test_parse_title() -> None:
    (element,) = parse_first_pass("#+title: Zettelkasten\n")
    assert isinstance(element, Title)
    assert element.value == "Zettelkasten"
    assert element.raw_line == "#+title: Zettelkasten\n"
    assert str(element) == "#+title: Zettelkasten\n"


def test_parse_title_strips_trailing_whitespace() -> None:
    (element,) = parse_first_pass("#+title: Spaced   \n")
    assert isinstance(element, Title)
    assert element.value == "Spaced"


def test_parse_headline_levels() -> None:
    elements = parse_first_pass("* One\n** Two\n*** Three\n")
    assert len(elements) == 3

    first, second, third = elements
    assert isinstance(first, Headline)
    assert first.level == 1
    assert first.title == "One"
    assert str(first) == "* One\n"

    assert isinstance(second, Headline)
    assert second.level == 2
    assert second.title == "Two"

    assert isinstance(third, Headline)
    assert third.level == 3
    assert third.title == "Three"


def test_headline_keeps_inner_stars() -> None:
    (element,) = parse_first_pass("* A * B\n")
    assert isinstance(element, Headline)
    assert element.title == "A * B"


def test_star_line_is_headline_not_list() -> None:
    (element,) = parse_first_pass("* not a list item\n")
    assert isinstance(element, Headline)
    assert not isinstance(element, ListItem)


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


def test_special_lines_do_not_absorb_following_lines() -> None:
    doc = "* Heading\n  indented text\n- item\n  continued\n"
    elements = parse_first_pass(doc)
    assert len(elements) == 4
    assert isinstance(elements[0], Headline)
    assert elements[1] == "  indented text\n"
    assert isinstance(elements[2], ListItem)
    assert elements[3] == "  continued\n"


def test_indented_special_lines_are_plain() -> None:
    lines = ["  #+title: x\n", "  * Head\n", "  - item\n"]
    assert parse_first_pass(lines) == lines


def test_special_lines_interleaved_with_other_structures() -> None:
    doc = (
        "#+title: Doc\n"
        "* Heading\n"
        ":PROPERTIES:\n"
        ":ID: 1\n"
        ":END:\n"
        "- item\n"
        "#+begin_src python\n"
        "x = 1\n"
        "#+end_src\n"
    )
    elements = parse_first_pass(doc)
    assert len(elements) == 5
    assert isinstance(elements[0], Title)
    assert isinstance(elements[1], Headline)
    assert isinstance(elements[2], PropertyDrawer)
    assert isinstance(elements[3], ListItem)
    assert isinstance(elements[4], Block)


def test_special_lines_input_variations() -> None:
    elements = parse_first_pass(b"#+title: Bytes\r\n* Head\r\n- item\r\n")
    assert isinstance(elements[0], Title)
    assert elements[0].value == "Bytes"
    assert isinstance(elements[1], Headline)
    assert elements[1].title == "Head"
    assert isinstance(elements[2], ListItem)
    assert elements[2].value == "item"

    (element,) = parse_first_pass(io.StringIO("#+title: Stream\n"))
    assert isinstance(element, Title)
    assert element.value == "Stream"
