"""Tests for title regular expressions in common_regex."""

from __future__ import annotations

from zettel_parser.common_regex import TITLE


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
