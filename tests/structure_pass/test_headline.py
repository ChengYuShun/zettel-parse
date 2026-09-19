"""Tests for the Headline structure pass element."""

from __future__ import annotations

from zettel_parser.first_pass import PropertyDrawer, parse_first_pass
from zettel_parser.first_pass_elements import Headline as FirstPassHeadline
from zettel_parser.structure_pass import Cursor
from zettel_parser.structure_pass_elements import Headline, Node


def _parse(doc: str) -> tuple[Headline, Cursor]:
    cursor = Cursor(parse_first_pass(doc))
    node = Headline.try_parse(cursor)
    assert node is not None
    return node, cursor


def test_returns_none_without_consuming() -> None:
    cursor = Cursor(["text\n"])
    assert Headline.try_parse(cursor) is None
    assert cursor.index == 0

    cursor = Cursor([])
    assert Headline.try_parse(cursor) is None
    assert cursor.index == 0


def test_simple_headline() -> None:
    node, cursor = _parse("* Title\n")
    assert node.level == 1
    assert node.title == "Title"
    assert node.properties is None
    assert node.body is None
    assert node.children == []
    assert cursor.index == 1


def test_headline_with_body() -> None:
    node, cursor = _parse("* Title\nBody line\n")
    assert node.body is not None
    assert str(node.body) == "Body line\n"
    assert cursor.index == 2


def test_headline_body_with_list() -> None:
    node, _ = _parse("* Title\n- item\n")
    assert node.body is not None
    assert str(node.body) == "- item\n"


def test_headline_with_property_drawer() -> None:
    doc = "* Title\n:PROPERTIES:\n:ID: 1\n:END:\nBody\n"
    node, cursor = _parse(doc)
    assert isinstance(node.properties, PropertyDrawer)
    assert node.properties["ID"] == "1"
    assert node.body is not None
    assert str(node.body) == "Body\n"
    assert cursor.index == 3


def test_property_drawer_must_be_immediate() -> None:
    doc = "* Title\n\n:PROPERTIES:\n:ID: 1\n:END:\n"
    node, cursor = _parse(doc)
    assert node.properties is None
    assert node.body is not None
    assert str(node.body) == "\n"
    assert cursor.index == 2


def test_children_are_collected() -> None:
    doc = "* A\n** B\n** C\n* D\n"
    node, cursor = _parse(doc)
    assert node.title == "A"
    assert [child.title for child in node.children] == ["B", "C"]
    assert isinstance(cursor.current, FirstPassHeadline)
    assert cursor.current.title == "D"


def test_deeper_headline_ends_children() -> None:
    doc = "* A\n** B\n* C\n"
    node, cursor = _parse(doc)
    assert [child.title for child in node.children] == ["B"]
    assert isinstance(cursor.current, FirstPassHeadline)
    assert cursor.current.title == "C"


def test_nested_recursion() -> None:
    doc = "* A\n** B\n*** C\n** D\n* E\n"
    node, cursor = _parse(doc)
    assert [child.title for child in node.children] == ["B", "D"]
    assert [child.title for child in node.children[0].children] == ["C"]
    assert node.children[1].children == []
    assert isinstance(cursor.current, FirstPassHeadline)
    assert cursor.current.title == "E"


def test_body_between_children() -> None:
    doc = "* A\n** B\nbody\n** C\n"
    node, _ = _parse(doc)
    first, second = node.children
    assert str(first.body) == "body\n"
    assert second.body is None


def test_headline_is_a_node() -> None:
    node = Headline(title="Title", level=2)
    assert isinstance(node, Node)
    assert node.title == "Title"
    assert node.level == 2
    assert node.properties is None
    assert node.body is None
    assert node.children == []
