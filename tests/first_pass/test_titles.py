"""First pass tests for title parsing."""

from __future__ import annotations

import io

from zettel_parser.first_pass import Cursor, Title, parse_first_pass


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


def test_title_among_other_structures() -> None:
    doc = "#+title: Doc\n* Heading\n- item\n"
    elements = parse_first_pass(doc)
    titles = [e for e in elements if isinstance(e, Title)]
    assert len(titles) == 1
    assert titles[0].value == "Doc"


def test_indented_title_is_plain() -> None:
    lines = ["  #+title: x\n"]
    assert parse_first_pass(lines) == lines


def test_title_from_bytes() -> None:
    (element,) = parse_first_pass(b"#+title: Bytes\r\n")
    assert isinstance(element, Title)
    assert element.value == "Bytes"


def test_title_from_stringio() -> None:
    (element,) = parse_first_pass(io.StringIO("#+title: Stream\n"))
    assert isinstance(element, Title)
    assert element.value == "Stream"


def test_title_try_parse() -> None:
    cursor = Cursor(["#+title: Doc\n", "tail\n"])
    title = Title.try_parse(cursor)
    assert isinstance(title, Title)
    assert title.value == "Doc"
    assert title.raw_line == "#+title: Doc\n"
    assert cursor.index == 1

    cursor = Cursor(["plain\n"])
    assert Title.try_parse(cursor) is None
    assert cursor.index == 0
