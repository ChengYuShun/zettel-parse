"""Tests for file tags regular expressions in common_regex."""

from __future__ import annotations

from zettel_parser.common_regex import FILETAGS


def test_filetags_regex() -> None:
    match = FILETAGS.match("#+filetags: :tag1:TAG2:tag3:\n")
    assert match is not None
    assert match.group("tags") == ":tag1:TAG2:tag3:"


def test_filetags_regex_is_case_insensitive() -> None:
    match = FILETAGS.match("#+FILETAGS: :a:b:\n")
    assert match is not None
    assert match.group("tags") == ":a:b:"


def test_filetags_regex_allows_spaces_in_tags() -> None:
    match = FILETAGS.match("#+filetags: :work:project alpha:\n")
    assert match is not None
    assert match.group("tags") == ":work:project alpha:"


def test_filetags_regex_requires_whitespace_after_keyword() -> None:
    assert FILETAGS.match("#+filetags::a:\n") is None


def test_filetags_regex_requires_colon_sequence() -> None:
    assert FILETAGS.match("#+filetags: tag1\n") is None
    assert FILETAGS.match("#+filetags: :\n") is None
    assert FILETAGS.match("#+filetags: :a:b\n") is None


def test_filetags_regex_requires_no_indentation() -> None:
    assert FILETAGS.match("  #+filetags: :a:\n") is None


def test_filetags_regex_allows_trailing_whitespace_and_crlf() -> None:
    match = FILETAGS.match("#+filetags: :a:b:  \r\n")
    assert match is not None
    assert match.group("tags") == ":a:b:"
