"""First pass tests for file tags parsing."""

from __future__ import annotations

from zettel_parser.first_pass import Cursor, FileTags, parse_first_pass


def test_parse_filetags() -> None:
    (element,) = parse_first_pass("#+filetags: :tag1:TAG2:tag3:\n")
    assert isinstance(element, FileTags)
    assert element.tags == ":tag1:TAG2:tag3:"
    assert element.raw_line == "#+filetags: :tag1:TAG2:tag3:\n"
    assert str(element) == "#+filetags: :tag1:TAG2:tag3:\n"


def test_filetags_are_case_sensitive() -> None:
    (element,) = parse_first_pass("#+filetags: :Work:work:WORK:\n")
    assert isinstance(element, FileTags)
    assert element.tags == ":Work:work:WORK:"


def test_filetags_may_include_spaces() -> None:
    (element,) = parse_first_pass("#+filetags: :project alpha:done:\n")
    assert isinstance(element, FileTags)
    assert element.tags == ":project alpha:done:"


def test_filetags_single_tag() -> None:
    (element,) = parse_first_pass("#+filetags: :only:\n")
    assert isinstance(element, FileTags)
    assert element.tags == ":only:"


def test_filetags_among_other_structures() -> None:
    doc = "#+filetags: :a:b:\n* Heading\n- item\n"
    elements = parse_first_pass(doc)
    filetags = [e for e in elements if isinstance(e, FileTags)]
    assert len(filetags) == 1
    assert filetags[0].tags == ":a:b:"


def test_indented_filetags_is_plain() -> None:
    lines = ["  #+filetags: :a:\n"]
    assert parse_first_pass(lines) == lines


def test_invalid_filetags_is_plain() -> None:
    lines = ["#+filetags: tag1\n", "#+filetags::a:\n"]
    assert parse_first_pass(lines) == lines


def test_filetags_from_bytes() -> None:
    (element,) = parse_first_pass(b"#+filetags: :a:b:\r\n")
    assert isinstance(element, FileTags)
    assert element.tags == ":a:b:"


def test_filetags_try_parse() -> None:
    cursor = Cursor(["#+filetags: :a:b:\n"])
    filetags = FileTags.try_parse(cursor)
    assert isinstance(filetags, FileTags)
    assert filetags.tags == ":a:b:"
    assert cursor.index == 1

    cursor = Cursor(["#+filetags: invalid\n"])
    assert FileTags.try_parse(cursor) is None
    assert cursor.index == 0
