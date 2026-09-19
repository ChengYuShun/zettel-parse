"""Tests for block-level LaTeX expression parsing."""

from __future__ import annotations

import io

from zettel_parser import LatexBlock, LatexBlockType, parse
from zettel_parser.common_regex import (
    LATEX_BLOCK_BEGIN,
    LATEX_BLOCK_END,
    LATEX_DELIMITERS,
)


def test_delimiters_mapping() -> None:
    assert LATEX_DELIMITERS == {
        "\\[": "\\]",
        "\\begin{equation*}": "\\end{equation*}",
        "\\begin{tikzcd}": "\\end{tikzcd}",
    }


def test_begin_regex_bracket_flavor() -> None:
    match = LATEX_BLOCK_BEGIN.match("\\[ a + b\n")
    assert match is not None
    assert match.group("delimiter") == "\\["
    assert match.group("content") == "a + b"


def test_begin_regex_environment_flavors() -> None:
    for environment in ("equation*", "tikzcd"):
        line = f"\\begin{{{environment}}} x\n"
        match = LATEX_BLOCK_BEGIN.match(line)
        assert match is not None
        assert match.group("delimiter") == f"\\begin{{{environment}}}"
        assert match.group("content") == "x"


def test_begin_regex_without_content() -> None:
    match = LATEX_BLOCK_BEGIN.match("\\[\n")
    assert match is not None
    assert match.group("delimiter") == "\\["
    assert match.group("content") == ""


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


def test_begin_regex_requires_no_indentation() -> None:
    assert LATEX_BLOCK_BEGIN.match("  \\[\n") is None
    assert LATEX_BLOCK_BEGIN.match("\t\\begin{tikzcd}\n") is None


def test_end_regex_requires_no_indentation_and_no_trailing_content() -> None:
    assert LATEX_BLOCK_END.match("  \\]\n") is None
    assert LATEX_BLOCK_END.match("\\] trailing\n") is None
    assert LATEX_BLOCK_END.match("\\end{equation*} trailing\n") is None
    assert LATEX_BLOCK_END.match("\\] \r\n") is not None


def test_parse_bracket_flavor() -> None:
    doc = "\\[\na + b\n\\]\n"
    elements = parse(doc)
    assert len(elements) == 1

    block = elements[0]
    assert isinstance(block, LatexBlock)
    assert block.type is LatexBlockType.BRACKET
    assert block.delimiter == "\\["
    assert block.end_delimiter == "\\]"
    assert block.text == doc
    assert str(block) == doc


def test_parse_equation_flavor() -> None:
    doc = "\\begin{equation*}\na = b\n\\end{equation*}\n"
    (block,) = parse(doc)
    assert isinstance(block, LatexBlock)
    assert block.type is LatexBlockType.EQUATION
    assert block.delimiter == "\\begin{equation*}"
    assert block.end_delimiter == "\\end{equation*}"
    assert block.text == doc


def test_parse_tikzcd_flavor() -> None:
    doc = "\\begin{tikzcd}\nA \\arrow[r] & B\n\\end{tikzcd}\n"
    (block,) = parse(doc)
    assert isinstance(block, LatexBlock)
    assert block.type is LatexBlockType.TIKZCD
    assert block.delimiter == "\\begin{tikzcd}"
    assert block.end_delimiter == "\\end{tikzcd}"
    assert block.text == doc


def test_block_type_is_recorded() -> None:
    cases = {
        "\\[\nx\n\\]\n": LatexBlockType.BRACKET,
        "\\begin{equation*}\nx\n\\end{equation*}\n": LatexBlockType.EQUATION,
        "\\begin{tikzcd}\nx\n\\end{tikzcd}\n": LatexBlockType.TIKZCD,
    }
    for doc, expected_type in cases.items():
        (block,) = parse(doc)
        assert isinstance(block, LatexBlock)
        assert block.type is expected_type


def test_content_may_follow_left_delimiter() -> None:
    doc = "\\[ a + b\nc + d\n\\]\n"
    (block,) = parse(doc)
    assert isinstance(block, LatexBlock)
    assert block.text == doc

    doc = "\\begin{equation*} a = b\nc = d\n\\end{equation*}\n"
    (block,) = parse(doc)
    assert isinstance(block, LatexBlock)
    assert block.text == doc


def test_single_line_expression_is_not_parsed() -> None:
    lines = ["\\[ a + b \\]\n"]
    assert parse(lines) == lines


def test_trailing_content_after_right_delimiter_is_not_parsed() -> None:
    lines = ["\\[\n", "a + b\n", "\\] trailing\n"]
    assert parse(lines) == lines


def test_indented_delimiters_are_not_parsed() -> None:
    lines = ["  \\[\n", "a + b\n", "  \\]\n"]
    assert parse(lines) == lines


def test_unclosed_expression_stays_as_lines() -> None:
    lines = ["\\[\n", "a + b\n", "* Heading\n"]
    assert parse(lines) == lines


def test_mismatched_environment_stays_as_lines() -> None:
    lines = ["\\begin{equation*}\n", "a = b\n", "\\end{tikzcd}\n"]
    assert parse(lines) == lines

    lines = ["\\[\n", "a + b\n", "\\end{equation*}\n"]
    assert parse(lines) == lines


def test_multiple_expressions() -> None:
    doc = (
        "\\[\nx\n\\]\n"
        "\\begin{tikzcd}\nA \\arrow[r] & B\n\\end{tikzcd}\n"
    )
    elements = parse(doc)
    assert len(elements) == 2
    assert isinstance(elements[0], LatexBlock)
    assert elements[0].delimiter == "\\["
    assert isinstance(elements[1], LatexBlock)
    assert elements[1].delimiter == "\\begin{tikzcd}"


def test_expressions_interleaved_with_other_structures() -> None:
    doc = (
        "Intro\n"
        "\\[\nx\n\\]\n"
        "Between\n"
        "#+begin_src python\n"
        "y = 1\n"
        "#+end_src\n"
    )
    elements = parse(doc)
    assert len(elements) == 4
    assert elements[0] == "Intro\n"
    assert isinstance(elements[1], LatexBlock)
    assert elements[2] == "Between\n"
    assert not isinstance(elements[3], LatexBlock)


def test_expression_without_trailing_newline() -> None:
    doc = "\\[\nx\n\\]"
    (block,) = parse(doc)
    assert isinstance(block, LatexBlock)
    assert block.text == doc


def test_latex_input_variations() -> None:
    raw_bytes = b"\\[\r\nx\r\n\\]\r\n"
    (block,) = parse(raw_bytes)
    assert isinstance(block, LatexBlock)
    assert block.delimiter == "\\["
    assert block.text == "\\[\r\nx\r\n\\]\r\n"

    (block,) = parse(io.StringIO("\\begin{tikzcd}\nA\n\\end{tikzcd}\n"))
    assert isinstance(block, LatexBlock)
    assert block.text == "\\begin{tikzcd}\nA\n\\end{tikzcd}\n"

    (block,) = parse([b"\\[\n", b"x\n", b"\\]\n"])
    assert isinstance(block, LatexBlock)
    assert block.text == "\\[\nx\n\\]\n"
