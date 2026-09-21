"""First pass tests for property drawer parsing."""

from __future__ import annotations

import io

import pytest

from zettel_parser.first_pass import (
    Cursor,
    Headline,
    NodeProperty,
    PropertyDrawer,
    Title,
    parse_first_pass,
)


def test_basic_property_drawer() -> None:
    doc = (
        "#+TITLE: Sample\n"
        ":PROPERTIES:\n"
        ":CUSTOM_ID: sec-1\n"
        ":ID: 12345\n"
        ":END:\n"
        "* Heading\n"
    )
    elements = parse_first_pass(doc)
    assert len(elements) == 3

    title = elements[0]
    assert isinstance(title, Title)
    assert title.value == "Sample"

    drawer = elements[1]
    assert isinstance(drawer, PropertyDrawer)
    assert drawer["CUSTOM_ID"] == "sec-1"
    assert drawer["ID"] == "12345"
    assert drawer.properties == {"CUSTOM_ID": "sec-1", "ID": "12345"}
    assert drawer.node_properties == [
        NodeProperty(name="CUSTOM_ID", value="sec-1"),
        NodeProperty(name="ID", value="12345"),
    ]
    assert drawer.indent == ""
    assert str(drawer) == (
        ":PROPERTIES:\n:CUSTOM_ID: sec-1\n:ID: 12345\n:END:\n"
    )

    headline = elements[2]
    assert isinstance(headline, Headline)
    assert headline.title == "Heading"


def test_property_names_are_case_insensitive() -> None:
    doc = ":properties:\n:Custom_Id: my-id\n:end:\n"
    (drawer,) = parse_first_pass(doc)
    assert isinstance(drawer, PropertyDrawer)
    assert drawer["CUSTOM_ID"] == "my-id"
    assert drawer["custom_id"] == "my-id"
    assert drawer["Custom_Id"] == "my-id"
    assert drawer.get("CUSTOM_ID") == "my-id"
    assert drawer.get("missing") is None
    assert drawer.properties == {"Custom_Id": "my-id"}


def test_indented_property_drawer() -> None:
    doc = (
        "* Heading\n"
        "  :PROPERTIES:\n"
        "  :ID: abc-999\n"
        "  :END:\n"
        "Body\n"
    )
    elements = parse_first_pass(doc)
    assert len(elements) == 3

    drawer = elements[1]
    assert isinstance(drawer, PropertyDrawer)
    assert drawer.indent == "  "
    assert drawer["ID"] == "abc-999"
    assert drawer.raw_lines == [
        "  :PROPERTIES:\n",
        "  :ID: abc-999\n",
        "  :END:\n",
    ]


def test_append_syntax_joins_values() -> None:
    doc = (
        ":PROPERTIES:\n"
        ":header-args: :results output\n"
        ":header-args+: :session py\n"
        ":header-args+: :tangle yes\n"
        ":END:\n"
    )
    (drawer,) = parse_first_pass(doc)
    assert isinstance(drawer, PropertyDrawer)
    assert drawer["header-args"] == ":results output :session py :tangle yes"
    assert [prop.append for prop in drawer.node_properties] == [
        False,
        True,
        True,
    ]


def test_append_to_missing_property_starts_value() -> None:
    doc = ":PROPERTIES:\n:header-args+: :session first\n:END:\n"
    (drawer,) = parse_first_pass(doc)
    assert isinstance(drawer, PropertyDrawer)
    assert drawer["header-args"] == ":session first"


def test_append_with_empty_value_keeps_existing() -> None:
    doc = ":PROPERTIES:\n:A: one\n:A+:\n:END:\n"
    (drawer,) = parse_first_pass(doc)
    assert isinstance(drawer, PropertyDrawer)
    assert drawer["A"] == "one"


def test_empty_property_drawer() -> None:
    (drawer,) = parse_first_pass(":PROPERTIES:\n:END:\n")
    assert isinstance(drawer, PropertyDrawer)
    assert drawer.properties == {}
    assert drawer.node_properties == []


def test_empty_property_values() -> None:
    doc = ":PROPERTIES:\n:EMPTY_VAL:\n:SPACED_VAL:   \n:END:\n"
    (drawer,) = parse_first_pass(doc)
    assert isinstance(drawer, PropertyDrawer)
    assert drawer["EMPTY_VAL"] == ""
    assert drawer["SPACED_VAL"] == ""


def test_duplicate_names_overwrite_and_keep_all() -> None:
    doc = ":PROPERTIES:\n:TAG: first\n:TAG: second\n:END:\n"
    (drawer,) = parse_first_pass(doc)
    assert isinstance(drawer, PropertyDrawer)
    assert drawer["TAG"] == "second"
    assert drawer.get_all("TAG") == ["first", "second"]
    assert drawer.get_all("tag") == ["first", "second"]


def test_unclosed_property_drawer_stays_lines() -> None:
    lines = [":PROPERTIES:\n", ":ID: 123\n", "plain text\n"]
    assert parse_first_pass(lines) == lines


def test_blank_line_inside_property_drawer_stays_lines() -> None:
    lines = [":PROPERTIES:\n", "\n", ":ID: 123\n", ":END:\n"]
    assert parse_first_pass(lines) == lines


def test_non_property_line_stays_lines() -> None:
    lines = [":PROPERTIES:\n", "This is not a property line.\n", ":END:\n"]
    assert parse_first_pass(lines) == lines


def test_other_drawer_name_is_not_parsed() -> None:
    lines = [":LOGBOOK:\n", ":ID: 1\n", ":END:\n"]
    assert parse_first_pass(lines) == lines


def test_multiple_property_drawers() -> None:
    doc = (
        ":PROPERTIES:\n"
        ":ROOT_ID: 0\n"
        ":END:\n"
        "* Sub 1\n"
        ":PROPERTIES:\n"
        ":SUB_ID: 1\n"
        ":END:\n"
    )
    elements = parse_first_pass(doc)
    assert len(elements) == 3

    root, headline, sub = elements
    assert isinstance(root, PropertyDrawer)
    assert isinstance(headline, Headline)
    assert isinstance(sub, PropertyDrawer)
    assert root["ROOT_ID"] == "0"
    assert headline.title == "Sub 1"
    assert sub["SUB_ID"] == "1"


def test_drawer_input_variations() -> None:
    (drawer,) = parse_first_pass(b":PROPERTIES:\n:ID: b1\n:END:\n")
    assert isinstance(drawer, PropertyDrawer)
    assert drawer["ID"] == "b1"

    (drawer,) = parse_first_pass(
        [b":PROPERTIES:\n", b":ID: b2\n", b":END:\n"]
    )
    assert isinstance(drawer, PropertyDrawer)
    assert drawer["ID"] == "b2"

    (drawer,) = parse_first_pass(
        io.StringIO(":PROPERTIES:\n:ID: sio\n:END:\n")
    )
    assert isinstance(drawer, PropertyDrawer)
    assert drawer["ID"] == "sio"

    (drawer,) = parse_first_pass(":PROPERTIES:\r\n:ID: crlf\r\n:END:\r\n")
    assert isinstance(drawer, PropertyDrawer)
    assert drawer["ID"] == "crlf"


def test_property_lookup() -> None:
    drawer = PropertyDrawer(
        node_properties=[
            NodeProperty(name="A", value="1"),
            NodeProperty(name="B", value="2"),
        ]
    )
    assert drawer.properties == {"A": "1", "B": "2"}
    assert list(drawer.properties) == ["A", "B"]
    assert list(drawer.properties.values()) == ["1", "2"]
    assert list(drawer.properties.items()) == [("A", "1"), ("B", "2")]
    assert drawer.get("a") == "1"
    assert drawer.get("missing", "def") == "def"

    with pytest.raises(KeyError):
        _ = drawer["NONEXISTENT"]


def test_try_parse() -> None:
    cursor = Cursor([":PROPERTIES:\n", ":ID: 1\n", ":END:\n", "* H\n"])
    drawer = PropertyDrawer.try_parse(cursor)
    assert isinstance(drawer, PropertyDrawer)
    assert drawer["ID"] == "1"
    assert cursor.index == 3


def test_try_parse_without_end_leaves_cursor() -> None:
    for lines in (
        [":PROPERTIES:\n", "\n", ":END:\n"],
        [":PROPERTIES:\n", "not a property\n", ":END:\n"],
        [":PROPERTIES:\n", ":ID: 1\n"],
    ):
        cursor = Cursor(list(lines))
        assert PropertyDrawer.try_parse(cursor) is None
        assert cursor.index == 0
