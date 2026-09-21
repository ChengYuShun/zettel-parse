"""Tests for the serialization dispatch API."""

from __future__ import annotations

import pytest

from zettel_parser.first_pass_elements import FileTags
from zettel_parser.serialization import (
    SERIALIZERS,
    Renderer,
    register_serializer,
    serialize,
    to_data,
    to_json,
    to_org,
    to_text,
    to_xml,
)
from zettel_parser.structure_pass import parse
from zettel_parser.structure_pass_elements import Zettel


def _ast() -> Zettel:
    return parse("#+title: Doc\n#+filetags: :a:b:\n\nHello *world*\n")


def test_default_format_is_json() -> None:
    ast = _ast()
    assert serialize(ast) == to_json(ast)


@pytest.mark.parametrize(
    ("fmt", "renderer"),
    [
        ("json", to_json),
        ("xml", to_xml),
        ("text", to_text),
        ("org", to_org),
    ],
)
def test_serialize_dispatches_on_fmt(fmt: str, renderer: Renderer) -> None:
    ast = _ast()
    assert serialize(ast, fmt) == renderer(ast)
    assert serialize(ast, fmt=fmt) == renderer(ast)


def test_registry_holds_the_builtin_formats() -> None:
    expected = {
        "json": to_json,
        "xml": to_xml,
        "text": to_text,
        "org": to_org,
    }
    assert expected == SERIALIZERS


def test_unknown_format_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unknown format 'yaml'"):
        serialize(_ast(), "yaml")


def test_register_serializer_extends_and_replaces() -> None:
    name = "test-format"
    calls: list[object] = []

    def renderer(node: object) -> str:
        calls.append(node)
        return "custom"

    try:
        register_serializer(name, renderer)
        assert SERIALIZERS[name] is renderer

        ast = _ast()
        assert serialize(ast, name) == "custom"
        assert calls == [ast]

        def replacement(node: object) -> str:
            return "replaced"

        register_serializer(name, replacement)
        assert serialize(ast, name) == "replaced"
    finally:
        SERIALIZERS.pop(name, None)


def test_to_xml_rejects_non_node_input() -> None:
    for node in (None, "text", [Zettel()]):
        with pytest.raises(TypeError):
            to_xml(node)


def test_to_data_rejects_first_pass_only_objects() -> None:
    with pytest.raises(TypeError):
        to_data(FileTags(tags=":a:"))
