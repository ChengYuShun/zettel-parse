"""Tests for the canonical intermediate representation."""

from __future__ import annotations

import pytest

from zettel_parser.first_pass_elements import (
    CheckboxState,
    LatexBlock,
    LatexBlockType,
)
from zettel_parser.serialization import to_data
from zettel_parser.structure_pass import parse
from zettel_parser.structure_pass_elements import ListItem, Zettel


def _tags(node: object) -> set[str]:
    """Collect every ``"type"`` tag appearing in a ``Data`` tree."""
    result: set[str] = set()

    def walk(value: object) -> None:
        if isinstance(value, dict):
            tag = value.get("type")
            if isinstance(tag, str):
                result.add(tag)
            for child in value.values():
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(to_data(node))
    return result


def test_none_and_plain_string_pass_through() -> None:
    assert to_data(None) is None
    assert to_data("hello") == "hello"


def test_zettel_is_tagged_first() -> None:
    data = to_data(parse("#+title: Doc\n"))
    assert isinstance(data, dict)
    assert list(data) == [
        "type",
        "title",
        "level",
        "filetags",
        "properties",
        "body",
        "children",
    ]
    assert data["type"] == "Zettel"
    assert data["title"] == "Doc"
    assert data["level"] == 0


def test_enums_are_rendered_as_values() -> None:
    latex = LatexBlock(
        type=LatexBlockType.BRACKET, delimiter=r"\[", text="\\[\n\\]\n"
    )
    assert to_data(latex) == {
        "type": "LatexBlock",
        "latex_type": "bracket",
        "delimiter": "\\[",
        "text": "\\[\n\\]\n",
    }

    item = ListItem(
        bullet="-", value="done", checked=CheckboxState.CHECKED
    )
    assert to_data(item)["checked"] == "checked"


def test_plain_strings_stay_bare_inside_inline_content() -> None:
    data = to_data(parse("a /b/\n"))
    assert isinstance(data, dict)
    body = data["body"]
    assert isinstance(body, dict)
    paragraph = body["elements"][0]
    assert isinstance(paragraph, dict)
    text = paragraph["elements"][0]
    assert isinstance(text, dict)
    assert text["type"] == "ParagraphText"
    assert text["elements"][0] == "a "
    assert text["elements"][1]["type"] == "Italic"


def test_all_structure_types_are_reachable() -> None:
    doc = (
        ":PROPERTIES:\n:ID: 1\n:END:\n"
        "#+title: Doc\n"
        "#+filetags: :a:b:\n"
        "text /em/\n"
        "- item\n"
        "\\[\nx\n\\]\n"
        "#+begin_src python\n"
        "x = 1\n"
        "#+end_src\n"
        "\n"
        "* Head\n"
    )
    tags = _tags(parse(doc))
    assert tags == {
        "Zettel",
        "Headline",
        "PropertyDrawer",
        "NodeProperty",
        "FlatText",
        "Paragraph",
        "ParagraphText",
        "Italic",
        "List",
        "ListItem",
        "LatexBlock",
        "Block",
        "BlankLines",
    }


def test_unsupported_object_raises_type_error() -> None:
    with pytest.raises(TypeError):
        to_data(object())


def test_hand_built_zettel_defaults() -> None:
    assert to_data(Zettel()) == {
        "type": "Zettel",
        "title": "",
        "level": 0,
        "filetags": [],
        "properties": None,
        "body": None,
        "children": [],
    }
