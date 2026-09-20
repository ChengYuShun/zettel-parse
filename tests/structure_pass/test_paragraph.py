"""Tests for the Paragraph structure pass element."""

from __future__ import annotations

from zettel_parser.first_pass import parse_first_pass
from zettel_parser.first_pass_elements import (
    Block,
    Headline,
    LatexBlock,
    LatexBlockType,
    Title,
)
from zettel_parser.inline_pass import Italic, Link
from zettel_parser.structure_pass import Cursor
from zettel_parser.structure_pass_elements import (
    List,
    Paragraph,
    ParagraphText,
)


def _make_list(doc: str) -> List:
    cursor = Cursor(parse_first_pass(doc))
    lst = List.try_parse(cursor)
    assert lst is not None
    return lst


def _latex_block() -> LatexBlock:
    return LatexBlock(
        type=LatexBlockType.BRACKET,
        delimiter=r"\[",
        text="\\[\nx = 1\n\\]\n",
    )


def _src_block() -> Block:
    return Block(
        name="src",
        arguments="python",
        raw_lines=["#+begin_src python\n", "x = 1\n", "#+end_src\n"],
    )


def test_paragraph_of_text_lines() -> None:
    cursor = Cursor(["line one\n", "line two\n", "\n", "next\n"])
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    assert paragraph.elements == [ParagraphText("line one\nline two\n")]
    assert str(paragraph) == "line one\nline two\n"
    assert cursor.index == 2


def test_consecutive_text_lines_form_one_paragraph_text() -> None:
    cursor = Cursor(["alpha\n", "beta\n", "gamma\n"])
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    assert len(paragraph.elements) == 1
    text = paragraph.elements[0]
    assert isinstance(text, ParagraphText)
    assert text.text == "alpha\nbeta\ngamma\n"
    assert cursor.index == 3


def test_paragraph_includes_latex_and_blocks() -> None:
    latex = _latex_block()
    block = _src_block()
    cursor = Cursor(["intro\n", latex, block, "\n", "outro\n"])
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    assert paragraph.elements == [ParagraphText("intro\n"), latex, block]
    assert str(paragraph) == "intro\n" + str(latex) + str(block)
    assert cursor.index == 3


def test_text_runs_around_block_are_separate() -> None:
    block = _src_block()
    cursor = Cursor(["before\n", block, "after\n"])
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    assert [type(element).__name__ for element in paragraph.elements] == [
        "ParagraphText",
        "Block",
        "ParagraphText",
    ]
    before = paragraph.elements[0]
    after = paragraph.elements[2]
    assert isinstance(before, ParagraphText)
    assert isinstance(after, ParagraphText)
    assert before.text == "before\n"
    assert after.text == "after\n"
    assert cursor.index == 3


def test_paragraph_can_start_with_latex_or_block() -> None:
    latex = _latex_block()
    cursor = Cursor([latex])
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    assert paragraph.elements == [latex]
    assert cursor.index == 1

    block = _src_block()
    cursor = Cursor([block])
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    assert paragraph.elements == [block]


def test_paragraph_from_first_pass_output() -> None:
    doc = (
        "Intro line\n"
        "\\[\n"
        "x = 1\n"
        "\\]\n"
        "#+begin_src python\n"
        "print(1)\n"
        "#+end_src\n"
        "\n"
        "After\n"
    )
    cursor = Cursor(parse_first_pass(doc))
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    assert [type(element).__name__ for element in paragraph.elements] == [
        "ParagraphText",
        "LatexBlock",
        "Block",
    ]
    assert cursor.index == 3
    assert cursor.peek() == "\n"


def test_terminates_at_blank_line() -> None:
    cursor = Cursor(["line\n", "   \n", "line\n"])
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    assert paragraph.elements == [ParagraphText("line\n")]
    assert cursor.index == 1


def test_returns_none_without_consuming() -> None:
    cursor = Cursor([Headline(level=1, title="Title", raw_line="* Title\n")])
    assert Paragraph.try_parse(cursor) is None
    assert cursor.index == 0

    cursor = Cursor([Title(value="Doc", raw_line="#+title: Doc\n")])
    assert Paragraph.try_parse(cursor) is None
    assert cursor.index == 0


def test_returns_none_at_end() -> None:
    cursor = Cursor([])
    assert Paragraph.try_parse(cursor) is None
    assert cursor.index == 0


def test_parses_paragraph_after_non_fitting_element() -> None:
    cursor = Cursor(
        [Headline(level=1, title="Title", raw_line="* Title\n"), "body\n"]
    )
    cursor.advance()
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    assert paragraph.elements == [ParagraphText("body\n")]


def test_paragraph_includes_list() -> None:
    lst = _make_list("- one\n- two\n")
    cursor = Cursor(["intro\n", lst, "\n", "after\n"])
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    assert [type(element).__name__ for element in paragraph.elements] == [
        "ParagraphText",
        "List",
    ]
    assert paragraph.elements[1] is lst
    assert str(paragraph) == "intro\n" + str(lst)
    assert cursor.index == 2
    assert cursor.current == "\n"


def test_paragraph_can_start_with_list() -> None:
    lst = _make_list("- one\n")
    cursor = Cursor([lst])
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    assert paragraph.elements == [lst]
    assert cursor.index == 1


def test_paragraph_accepts_list_with_internal_blank_lines() -> None:
    lst = _make_list("- one\n\n- two\n")
    cursor = Cursor([lst, "tail\n"])
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    assert paragraph.elements == [lst, ParagraphText("tail\n")]
    assert cursor.index == 2


def test_paragraph_mixes_text_block_and_list() -> None:
    block = _src_block()
    lst = _make_list("- one\n")
    cursor = Cursor(["text\n", block, lst, "\n"])
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    assert [type(element).__name__ for element in paragraph.elements] == [
        "ParagraphText",
        "Block",
        "List",
    ]
    assert cursor.index == 3


def test_paragraph_text_inline_elements_roundtrip() -> None:
    cursor = Cursor(["hello *world*\n"])
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    text = paragraph.elements[0]
    assert isinstance(text, ParagraphText)
    assert "".join(str(element) for element in text.elements) == text.text


def test_paragraph_text_inline_elements_are_parsed() -> None:
    cursor = Cursor(["a /b/ [[c][d]]\n"])
    paragraph = Paragraph.try_parse(cursor)
    assert paragraph is not None
    text = paragraph.elements[0]
    assert isinstance(text, ParagraphText)
    assert text.elements == [
        "a ",
        Italic(elements=["b"]),
        " ",
        Link(target="c", description=["d"]),
        "\n",
    ]
