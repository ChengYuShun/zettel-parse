"""Tests for LaTeX block regular expressions in common_regex."""

from __future__ import annotations

from zettel_parser.common_regex import (
    LATEX_BLOCK_BEGIN,
    LATEX_BLOCK_DELIMITERS,
    LATEX_BLOCK_END,
)


def test_block_delimiters() -> None:
    assert LATEX_BLOCK_DELIMITERS == (
        ("\\[", "\\]", "BRACKET"),
        ("\\begin{equation*}", "\\end{equation*}", "EQUATION"),
        ("\\begin{tikzcd}", "\\end{tikzcd}", "TIKZCD"),
        ("\\begin{align*}", "\\end{align*}", "ALIGN"),
    )


def test_begin_regex_bracket_flavor() -> None:
    match = LATEX_BLOCK_BEGIN.match("\\[ a + b\n")
    assert match is not None
    assert match.group("delimiter") == "\\["
    assert match.group("content") == " a + b"


def test_begin_regex_environment_flavors() -> None:
    for environment in ("equation*", "tikzcd", "align*"):
        line = f"\\begin{{{environment}}} x\n"
        match = LATEX_BLOCK_BEGIN.match(line)
        assert match is not None
        assert match.group("delimiter") == f"\\begin{{{environment}}}"
        assert match.group("content") == " x"


def test_begin_regex_without_content() -> None:
    match = LATEX_BLOCK_BEGIN.match("\\[\n")
    assert match is not None
    assert match.group("delimiter") == "\\["
    assert match.group("content") == ""


def test_begin_regex_keeps_surrounding_whitespace_in_content() -> None:
    match = LATEX_BLOCK_BEGIN.match("\\[  a + b  \n")
    assert match is not None
    assert match.group("content") == "  a + b  "


def test_end_regex_flavors() -> None:
    bracket = LATEX_BLOCK_END.match("\\]\n")
    assert bracket is not None
    assert bracket.group("delimiter") == "\\]"

    equation = LATEX_BLOCK_END.match("\\end{equation*}\n")
    assert equation is not None
    assert equation.group("delimiter") == "\\end{equation*}"

    tikzcd = LATEX_BLOCK_END.match("\\end{tikzcd}\n")
    assert tikzcd is not None
    assert tikzcd.group("delimiter") == "\\end{tikzcd}"

    align = LATEX_BLOCK_END.match("\\end{align*}\n")
    assert align is not None
    assert align.group("delimiter") == "\\end{align*}"


def test_begin_regex_rejects_indentation() -> None:
    for indent in (" ", "  ", "\t", " \t "):
        assert LATEX_BLOCK_BEGIN.match(f"{indent}\\[ a + b\n") is None
        assert LATEX_BLOCK_BEGIN.match(f"{indent}\\begin{{tikzcd}} x\n") is None
        assert LATEX_BLOCK_BEGIN.match(f"{indent}\\begin{{align*}} x\n") is None


def test_end_regex_rejects_indentation_and_trailing_content() -> None:
    for indent in (" ", "  ", "\t", " \t "):
        assert LATEX_BLOCK_END.match(f"{indent}\\]\n") is None
        assert LATEX_BLOCK_END.match(f"{indent}\\end{{equation*}}\n") is None
        assert LATEX_BLOCK_END.match(f"{indent}\\end{{align*}}\n") is None

    assert LATEX_BLOCK_END.match("\\] trailing\n") is None
    assert LATEX_BLOCK_END.match("\\end{equation*} trailing\n") is None
    assert LATEX_BLOCK_END.match("\\end{align*} trailing\n") is None
    assert LATEX_BLOCK_END.match("\\] \r\n") is not None
