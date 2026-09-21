"""Tests for the Zettel structure pass element."""

from __future__ import annotations

from zettel_parser.first_pass import PropertyDrawer, parse_first_pass
from zettel_parser.structure_pass import Cursor
from zettel_parser.structure_pass_elements import Headline, Node, Zettel


def _parse(doc: str) -> Zettel:
    return Zettel.try_parse(Cursor(parse_first_pass(doc)))


def test_empty_document() -> None:
    node = _parse("")
    assert node.level == 0
    assert node.title == ""
    assert node.filetags == ""
    assert node.properties is None
    assert node.body is None
    assert node.children == []


def test_title_and_filetags() -> None:
    node = _parse("#+title: Doc\n#+filetags: :a:b:\n")
    assert node.title == "Doc"
    assert node.filetags == ":a:b:"


def test_later_title_and_filetags_override_earlier() -> None:
    node = _parse(
        "#+title: First\n"
        "#+filetags: :x:\n"
        "#+title: Second\n"
        "#+filetags: :y:z:\n"
    )
    assert node.title == "Second"
    assert node.filetags == ":y:z:"


def test_property_drawer_before_title() -> None:
    doc = ":PROPERTIES:\n:ID: 1\n:END:\n#+title: Doc\n"
    node = _parse(doc)
    assert isinstance(node.properties, PropertyDrawer)
    assert node.properties["ID"] == "1"
    assert node.title == "Doc"


def test_body_and_children() -> None:
    doc = "#+title: Doc\nIntro\n\n* A\n** B\n* C\n"
    node = _parse(doc)
    assert node.title == "Doc"
    assert node.body is not None
    assert str(node.body) == "Intro\n\n"
    assert [child.title for child in node.children] == ["A", "C"]
    assert [child.title for child in node.children[0].children] == ["B"]


def test_only_headlines() -> None:
    node = _parse("* A\n* B\n")
    assert node.title == ""
    assert node.body is None
    assert [child.title for child in node.children] == ["A", "B"]


def test_body_before_headlines() -> None:
    node = _parse("Intro text\n\n* A\n")
    assert node.body is not None
    assert str(node.body) == "Intro text\n\n"
    assert [child.title for child in node.children] == ["A"]


def test_zettel_is_a_node() -> None:
    node = Zettel(title="Doc", filetags=":a:")
    assert isinstance(node, Node)
    assert node.level == 0
    assert node.title == "Doc"
    assert node.filetags == ":a:"
    assert node.properties is None
    assert node.body is None
    assert node.children == []


def test_zettel_children_are_headlines() -> None:
    node = _parse("* A\n** B\n")
    assert all(isinstance(child, Headline) for child in node.children)
