"""Tests for block regular expressions in common_regex."""

from __future__ import annotations

from zettel_parser.common_regex import BLOCK_BEGIN, BLOCK_END


def test_block_begin_regex_with_arguments() -> None:
    match = BLOCK_BEGIN.match("#+begin_src python :results output\n")
    assert match is not None
    assert match.group("name") == "src"
    assert match.group("args") == "python :results output"


def test_block_begin_regex_without_arguments() -> None:
    match = BLOCK_BEGIN.match("#+begin_example\n")
    assert match is not None
    assert match.group("name") == "example"
    assert match.group("args") is None


def test_block_regex_is_case_insensitive() -> None:
    match = BLOCK_BEGIN.match("#+BEGIN_SRC\n")
    assert match is not None
    assert match.group("name") == "SRC"
    assert BLOCK_END.match("#+END_SRC\n") is not None


def test_block_regex_rejects_indentation() -> None:
    for indent in (" ", "  ", "\t", " \t "):
        assert BLOCK_BEGIN.match(f"{indent}#+begin_src python\n") is None
        assert BLOCK_END.match(f"{indent}#+end_src\n") is None


def test_block_regex_rejects_unrelated_lines() -> None:
    assert BLOCK_BEGIN.match("#+title: hello\n") is None
    assert BLOCK_BEGIN.match("#+begin_\n") is None


def test_block_regex_allows_trailing_whitespace_and_crlf() -> None:
    match = BLOCK_BEGIN.match("#+begin_src python  \r\n")
    assert match is not None
    assert match.group("name") == "src"
    assert match.group("args") == "python"
    assert BLOCK_END.match("#+end_src \r\n") is not None
