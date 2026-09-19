"""First pass tests for block parsing and block regexes."""

from __future__ import annotations

import io

from zettel_parser.common_regex import BLOCK_BEGIN, BLOCK_END
from zettel_parser.first_pass import Block, PropertyDrawer, parse_first_pass


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


def test_block_regex_requires_no_indentation() -> None:
    assert BLOCK_BEGIN.match("  #+begin_src\n") is None
    assert BLOCK_BEGIN.match("\t#+begin_src\n") is None
    assert BLOCK_END.match("  #+end_src\n") is None


def test_block_regex_rejects_unrelated_lines() -> None:
    assert BLOCK_BEGIN.match("#+title: hello\n") is None
    assert BLOCK_BEGIN.match("#+begin_\n") is None


def test_block_regex_allows_trailing_whitespace_and_crlf() -> None:
    match = BLOCK_BEGIN.match("#+begin_src python  \r\n")
    assert match is not None
    assert match.group("name") == "src"
    assert match.group("args") == "python"
    assert BLOCK_END.match("#+end_src \r\n") is not None


def test_simple_src_block() -> None:
    doc = '#+begin_src python\nprint("hello")\n#+end_src\n'
    elements = parse_first_pass(doc)
    assert len(elements) == 1

    block = elements[0]
    assert isinstance(block, Block)
    assert block.name == "src"
    assert block.arguments == "python"
    assert block.body == 'print("hello")\n'
    assert block.body_lines == ['print("hello")\n']
    assert str(block) == doc
    assert block.raw_lines == [
        "#+begin_src python\n",
        'print("hello")\n',
        "#+end_src\n",
    ]


def test_block_without_arguments() -> None:
    doc = "#+begin_example\nfoo\n#+end_example\n"
    (block,) = parse_first_pass(doc)
    assert isinstance(block, Block)
    assert block.name == "example"
    assert block.arguments == ""
    assert block.body == "foo\n"


def test_block_with_header_arguments() -> None:
    doc = (
        "#+begin_src emacs-lisp :results output :exports both\n"
        '(message "hi")\n'
        "#+end_src\n"
    )
    (block,) = parse_first_pass(doc)
    assert isinstance(block, Block)
    assert block.arguments == "emacs-lisp :results output :exports both"


def test_block_name_is_normalized_to_lower_case() -> None:
    doc = "#+BEGIN_SRC js\nx\n#+END_SRC\n"
    (block,) = parse_first_pass(doc)
    assert isinstance(block, Block)
    assert block.name == "src"
    assert str(block) == doc


def test_end_name_matches_begin_name_case_insensitively() -> None:
    doc = "#+begin_src python\nx\n#+end_SRC\n"
    (block,) = parse_first_pass(doc)
    assert isinstance(block, Block)
    assert block.name == "src"


def test_multiline_body_with_blank_and_markup_lines() -> None:
    doc = (
        "#+begin_example\n"
        "line one\n"
        "\n"
        "* not a heading here\n"
        "#+title: not a keyword here\n"
        "#+end_example\n"
    )
    (block,) = parse_first_pass(doc)
    assert isinstance(block, Block)
    assert block.body_lines == [
        "line one\n",
        "\n",
        "* not a heading here\n",
        "#+title: not a keyword here\n",
    ]
    assert block.body == (
        "line one\n\n* not a heading here\n#+title: not a keyword here\n"
    )


def test_unclosed_block_stays_as_lines() -> None:
    lines = ["#+begin_src python\n", "x = 1\n", "plain text\n"]
    assert parse_first_pass(lines) == lines


def test_mismatched_end_stays_as_lines() -> None:
    lines = ["#+begin_src python\n", "x = 1\n", "#+end_example\n"]
    assert parse_first_pass(lines) == lines


def test_indented_block_is_not_parsed() -> None:
    lines = ["  #+begin_src python\n", "x = 1\n", "  #+end_src\n"]
    assert parse_first_pass(lines) == lines


def test_nested_blocks_of_different_types() -> None:
    doc = (
        "#+begin_quote\n"
        "#+begin_src python\n"
        "x = 1\n"
        "#+end_src\n"
        "#+end_quote\n"
    )
    (block,) = parse_first_pass(doc)
    assert isinstance(block, Block)
    assert block.name == "quote"
    assert block.body_lines == ["#+begin_src python\n", "x = 1\n", "#+end_src\n"]


def test_blocks_interleaved_with_other_lines() -> None:
    doc = (
        "Intro text\n"
        "#+begin_src python\n"
        "x = 1\n"
        "#+end_src\n"
        "Between text\n"
        "#+begin_example\n"
        "y\n"
        "#+end_example\n"
        "Outro text\n"
    )
    elements = parse_first_pass(doc)
    assert len(elements) == 5
    assert elements[0] == "Intro text\n"
    assert isinstance(elements[1], Block)
    assert elements[1].name == "src"
    assert elements[2] == "Between text\n"
    assert isinstance(elements[3], Block)
    assert elements[3].name == "example"
    assert elements[4] == "Outro text\n"


def test_blocks_and_property_drawers_together() -> None:
    doc = (
        ":PROPERTIES:\n"
        ":ID: 1\n"
        ":END:\n"
        "#+begin_src python\n"
        "x = 1\n"
        "#+end_src\n"
    )
    elements = parse_first_pass(doc)
    assert len(elements) == 2
    assert isinstance(elements[0], PropertyDrawer)
    assert isinstance(elements[1], Block)


def test_block_input_variations() -> None:
    raw_bytes = b"#+begin_src python\r\nx = 1\r\n#+end_src\r\n"
    (block,) = parse_first_pass(raw_bytes)
    assert isinstance(block, Block)
    assert block.raw_lines == [
        "#+begin_src python\r\n",
        "x = 1\r\n",
        "#+end_src\r\n",
    ]

    (block,) = parse_first_pass(io.StringIO("#+begin_example\nfoo\n#+end_example\n"))
    assert isinstance(block, Block)
    assert block.body == "foo\n"

    (block,) = parse_first_pass(
        [b"#+begin_src python\n", b"x = 1\n", b"#+end_src\n"]
    )
    assert isinstance(block, Block)
    assert block.name == "src"
    assert block.body == "x = 1\n"
