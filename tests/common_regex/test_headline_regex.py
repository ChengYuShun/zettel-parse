"""Tests for headline regular expressions in common_regex."""

from __future__ import annotations

from zettel_parser.common_regex import HEADLINE


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
