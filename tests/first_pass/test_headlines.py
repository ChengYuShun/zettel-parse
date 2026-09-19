"""First pass tests for headline parsing."""

from __future__ import annotations

from zettel_parser.first_pass import Cursor, Headline, ListItem, parse_first_pass


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


def test_headline_among_other_structures() -> None:
    doc = "#+title: Doc\n* Heading\n- item\n"
    elements = parse_first_pass(doc)
    headlines = [e for e in elements if isinstance(e, Headline)]
    assert len(headlines) == 1
    assert headlines[0].title == "Heading"


def test_headline_does_not_absorb_following_lines() -> None:
    doc = "* Heading\n  indented text\n"
    elements = parse_first_pass(doc)
    assert len(elements) == 2
    assert isinstance(elements[0], Headline)
    assert elements[1] == "  indented text\n"


def test_indented_headline_is_plain() -> None:
    lines = ["  * Head\n"]
    assert parse_first_pass(lines) == lines


def test_headline_from_bytes() -> None:
    (element,) = parse_first_pass(b"* Head\r\n")
    assert isinstance(element, Headline)
    assert element.title == "Head"


def test_headline_try_parse() -> None:
    cursor = Cursor(["*** Deep\n"])
    headline = Headline.try_parse(cursor)
    assert isinstance(headline, Headline)
    assert headline.level == 3
    assert headline.title == "Deep"
    assert cursor.index == 1

    cursor = Cursor(["  * Indented\n"])
    assert Headline.try_parse(cursor) is None
    assert cursor.index == 0
