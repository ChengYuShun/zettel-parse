"""First pass tests for block-level LaTeX expression parsing."""

from __future__ import annotations

import io

from zettel_parser.first_pass import (
    LatexBlock,
    LatexBlockType,
    parse_first_pass,
)


def test_parse_bracket_flavor() -> None:
    doc = "\\[\na + b\n\\]\n"
    elements = parse_first_pass(doc)
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
    (block,) = parse_first_pass(doc)
    assert isinstance(block, LatexBlock)
    assert block.type is LatexBlockType.EQUATION
    assert block.delimiter == "\\begin{equation*}"
    assert block.end_delimiter == "\\end{equation*}"
    assert block.text == doc


def test_parse_tikzcd_flavor() -> None:
    doc = "\\begin{tikzcd}\nA \\arrow[r] & B\n\\end{tikzcd}\n"
    (block,) = parse_first_pass(doc)
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
        (block,) = parse_first_pass(doc)
        assert isinstance(block, LatexBlock)
        assert block.type is expected_type


def test_content_may_follow_left_delimiter() -> None:
    doc = "\\[ a + b\nc + d\n\\]\n"
    (block,) = parse_first_pass(doc)
    assert isinstance(block, LatexBlock)
    assert block.text == doc

    doc = "\\begin{equation*} a = b\nc = d\n\\end{equation*}\n"
    (block,) = parse_first_pass(doc)
    assert isinstance(block, LatexBlock)
    assert block.text == doc


def test_single_line_expression_is_not_parsed() -> None:
    lines = ["\\[ a + b \\]\n"]
    assert parse_first_pass(lines) == lines


def test_trailing_content_after_right_delimiter_is_not_parsed() -> None:
    lines = ["\\[\n", "a + b\n", "\\] trailing\n"]
    assert parse_first_pass(lines) == lines


def test_indented_delimiters_are_not_parsed() -> None:
    lines = ["  \\[\n", "a + b\n", "  \\]\n"]
    assert parse_first_pass(lines) == lines


def test_unclosed_expression_stays_as_lines() -> None:
    lines = ["\\[\n", "a + b\n", "plain text\n"]
    assert parse_first_pass(lines) == lines


def test_mismatched_environment_stays_as_lines() -> None:
    lines = ["\\begin{equation*}\n", "a = b\n", "\\end{tikzcd}\n"]
    assert parse_first_pass(lines) == lines

    lines = ["\\[\n", "a + b\n", "\\end{equation*}\n"]
    assert parse_first_pass(lines) == lines


def test_multiple_expressions() -> None:
    doc = (
        "\\[\nx\n\\]\n"
        "\\begin{tikzcd}\nA \\arrow[r] & B\n\\end{tikzcd}\n"
    )
    elements = parse_first_pass(doc)
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
    elements = parse_first_pass(doc)
    assert len(elements) == 4
    assert elements[0] == "Intro\n"
    assert isinstance(elements[1], LatexBlock)
    assert elements[2] == "Between\n"
    assert not isinstance(elements[3], LatexBlock)


def test_expression_without_trailing_newline() -> None:
    doc = "\\[\nx\n\\]"
    (block,) = parse_first_pass(doc)
    assert isinstance(block, LatexBlock)
    assert block.text == doc


def test_latex_input_variations() -> None:
    raw_bytes = b"\\[\r\nx\r\n\\]\r\n"
    (block,) = parse_first_pass(raw_bytes)
    assert isinstance(block, LatexBlock)
    assert block.delimiter == "\\["
    assert block.text == "\\[\r\nx\r\n\\]\r\n"

    (block,) = parse_first_pass(io.StringIO("\\begin{tikzcd}\nA\n\\end{tikzcd}\n"))
    assert isinstance(block, LatexBlock)
    assert block.text == "\\begin{tikzcd}\nA\n\\end{tikzcd}\n"

    (block,) = parse_first_pass([b"\\[\n", b"x\n", b"\\]\n"])
    assert isinstance(block, LatexBlock)
    assert block.text == "\\[\nx\n\\]\n"
