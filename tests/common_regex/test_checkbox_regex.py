"""Tests for the checklist checkbox regular expression in common_regex."""

from __future__ import annotations

from zettel_parser.common_regex import CHECKBOX


def test_unchecked_marker() -> None:
    match = CHECKBOX.match("[ ]")
    assert match is not None
    assert match.group("mark") == " "


def test_checked_marker() -> None:
    match = CHECKBOX.match("[X]")
    assert match is not None
    assert match.group("mark") == "X"


def test_partial_marker() -> None:
    match = CHECKBOX.match("[-]")
    assert match is not None
    assert match.group("mark") == "-"


def test_marker_may_be_followed_by_space() -> None:
    for text, mark in (("[ ] task", " "), ("[X] done", "X"), ("[-] part", "-")):
        match = CHECKBOX.match(text)
        assert match is not None
        assert match.group("mark") == mark
        assert match.end() == 3


def test_marker_may_end_a_line() -> None:
    for text, mark in (("[ ]\n", " "), ("[X]\n", "X"), ("[-]\n", "-")):
        match = CHECKBOX.match(text)
        assert match is not None
        assert match.group("mark") == mark


def test_marker_must_be_followed_by_space_or_end() -> None:
    assert CHECKBOX.match("[ ]x") is None
    assert CHECKBOX.match("[X]extra") is None
    assert CHECKBOX.match("[ ]\ttab") is None


def test_marker_requires_lowercase_x_to_be_uppercase() -> None:
    assert CHECKBOX.match("[x]") is None
    assert CHECKBOX.match("[x] done") is None


def test_marker_rejects_other_contents() -> None:
    assert CHECKBOX.match("[]") is None
    assert CHECKBOX.match("[  ]") is None
    assert CHECKBOX.match("[Y]") is None
    assert CHECKBOX.match("") is None
    assert CHECKBOX.match("plain text") is None
