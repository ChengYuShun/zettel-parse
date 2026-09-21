"""First pass tests for the restricted list item content parser."""

from __future__ import annotations

from zettel_parser.first_pass import ListItemFirstPassParser


def test_parses_list_content_structures() -> None:
    elements = ListItemFirstPassParser().parse(
        "#+title: Not parsed\n"
        "#+filetags: :a:\n"
        "- nested\n"
        "#+begin_src python\n"
        "x = 1\n"
        "#+end_src\n"
        "\\[\n"
        "y\n"
        "\\]\n"
    )
    assert [type(element).__name__ for element in elements] == [
        "str",
        "str",
        "ListItem",
        "Block",
        "LatexBlock",
    ]


def test_keeps_plain_lines() -> None:
    assert ListItemFirstPassParser().parse("just text\n") == ["just text\n"]


def test_first_element_is_never_a_list_item() -> None:
    assert ListItemFirstPassParser().parse("- nested\n") == ["- nested\n"]
    assert ListItemFirstPassParser().parse("+ nested\n") == ["+ nested\n"]


def test_star_bullet_is_a_list_item_in_list_context() -> None:
    elements = ListItemFirstPassParser().parse("text\n* nested\n")
    assert [type(element).__name__ for element in elements] == [
        "str",
        "ListItem",
    ]
