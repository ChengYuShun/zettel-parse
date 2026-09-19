"""Tests for the cursor-driven first-pass element parsers."""

from __future__ import annotations

from zettel_parser.first_pass import (
    Block,
    Cursor,
    FileTags,
    Headline,
    LatexBlock,
    LatexBlockType,
    ListItem,
    PropertyDrawer,
    Title,
)


def test_cursor_navigation() -> None:
    cursor: Cursor[str] = Cursor(["a\n", "b\n"])
    assert cursor.current == "a\n"
    assert cursor.peek() == "a\n"
    assert cursor.peek(1) == "b\n"
    assert cursor.peek(5) is None
    assert cursor.peek(-1) is None
    assert not cursor.at_end

    cursor.advance()
    assert cursor.current == "b\n"
    cursor.advance()
    assert cursor.at_end
    assert cursor.current is None


def test_cursor_from_first_pass_module() -> None:
    from zettel_parser.cursor import Cursor as SharedCursor

    assert Cursor is SharedCursor


def test_title_try_parse() -> None:
    cursor = Cursor(["#+title: Doc\n", "tail\n"])
    title = Title.try_parse(cursor)
    assert isinstance(title, Title)
    assert title.value == "Doc"
    assert title.raw_line == "#+title: Doc\n"
    assert cursor.index == 1

    cursor = Cursor(["plain\n"])
    assert Title.try_parse(cursor) is None
    assert cursor.index == 0


def test_filetags_try_parse() -> None:
    cursor = Cursor(["#+filetags: :a:b:\n"])
    filetags = FileTags.try_parse(cursor)
    assert isinstance(filetags, FileTags)
    assert filetags.tags == ["a", "b"]
    assert cursor.index == 1

    cursor = Cursor(["#+filetags: invalid\n"])
    assert FileTags.try_parse(cursor) is None
    assert cursor.index == 0


def test_headline_try_parse() -> None:
    cursor = Cursor(["*** Deep\n"])
    headline = Headline.try_parse(cursor)
    assert isinstance(headline, Headline)
    assert headline.level == 3
    assert headline.title == "Deep"
    assert cursor.index == 1

    cursor = Cursor(["  * Indented\n"])
    assert Headline.try_parse(cursor) is None
    assert cursor.index == 0


def test_list_item_try_parse() -> None:
    cursor = Cursor(["- item\n"])
    item = ListItem.try_parse(cursor)
    assert isinstance(item, ListItem)
    assert item.bullet == "-"
    assert item.value == "item"
    assert cursor.index == 1

    cursor = Cursor(["  - indented\n"])
    assert ListItem.try_parse(cursor) is None
    assert cursor.index == 0


def test_property_drawer_try_parse() -> None:
    cursor = Cursor([":PROPERTIES:\n", ":ID: 1\n", ":END:\n", "* H\n"])
    drawer = PropertyDrawer.try_parse(cursor)
    assert isinstance(drawer, PropertyDrawer)
    assert drawer["ID"] == "1"
    assert cursor.index == 3


def test_property_drawer_try_parse_invalid_leaves_cursor() -> None:
    for lines in (
        [":PROPERTIES:\n", "\n", ":END:\n"],
        [":PROPERTIES:\n", "not a property\n", ":END:\n"],
        [":PROPERTIES:\n", ":ID: 1\n"],
    ):
        cursor = Cursor(list(lines))
        assert PropertyDrawer.try_parse(cursor) is None
        assert cursor.index == 0
        assert cursor.elements == lines


def test_block_try_parse() -> None:
    cursor = Cursor(["#+begin_src python\n", "x = 1\n", "#+end_src\n"])
    block = Block.try_parse(cursor)
    assert isinstance(block, Block)
    assert block.name == "src"
    assert block.arguments == "python"
    assert cursor.index == 3


def test_block_try_parse_without_end_leaves_cursor() -> None:
    for lines in (
        ["#+begin_src\n", "x\n"],
        ["#+begin_src\n", "x\n", "#+end_example\n"],
        ["  #+begin_src\n", "x\n", "  #+end_src\n"],
    ):
        cursor = Cursor(list(lines))
        assert Block.try_parse(cursor) is None
        assert cursor.index == 0


def test_latex_block_try_parse() -> None:
    cursor = Cursor(["\\[\n", "x\n", "\\]\n"])
    block = LatexBlock.try_parse(cursor)
    assert isinstance(block, LatexBlock)
    assert block.type is LatexBlockType.BRACKET
    assert cursor.index == 3


def test_latex_block_try_parse_without_end_leaves_cursor() -> None:
    for lines in (
        ["\\begin{equation*}\n", "x\n", "\\end{tikzcd}\n"],
        ["\\[\n", "x\n"],
        ["  \\[\n", "x\n", "  \\]\n"],
    ):
        cursor = Cursor(list(lines))
        assert LatexBlock.try_parse(cursor) is None
        assert cursor.index == 0
